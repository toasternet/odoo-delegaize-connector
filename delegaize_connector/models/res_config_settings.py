# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).
import json
import logging

import requests

from odoo import _, fields, models

from .delegaize_mixin import DEFAULT_API_PATH, DEFAULT_LINK_PATH, DEFAULT_URL

_logger = logging.getLogger(__name__)

TIMEOUT = 15


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    delegaize_url = fields.Char(
        string="DelegAIze address",
        config_parameter="delegaize_connector.url",
        default=DEFAULT_URL,
        help="Address of your DelegAIze workspace, e.g. https://delegaize.innov-ai-tive.de",
    )
    delegaize_api_key = fields.Char(
        string="DelegAIze API key",
        config_parameter="delegaize_connector.api_key",
        help="API key of a DelegAIze user (ideally a technical user). It is only used "
             "for the connection test; the buttons on records do not use it.",
    )
    delegaize_link_path = fields.Char(
        string="Deep link path",
        config_parameter="delegaize_connector.link_path",
        default=DEFAULT_LINK_PATH,
        help="Path in DelegAIze that receives the record reference.",
    )
    delegaize_api_path = fields.Char(
        string="API path",
        config_parameter="delegaize_connector.api_path",
        default=DEFAULT_API_PATH,
        help="Path of the DelegAIze API used by the connection test.",
    )
    delegaize_send_record_name = fields.Boolean(
        string="Include record name in links",
        config_parameter="delegaize_connector.send_record_name",
        default=True,
        help="If enabled, the display name of the record (e.g. the company name) is part "
             "of the link, so DelegAIze can find the record before it is linked.",
    )

    # ------------------------------------------------------------------
    def _delegaize_notify(self, title, message, kind):
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {"title": title, "message": message, "type": kind, "sticky": kind != "success"},
        }

    @staticmethod
    def _delegaize_parse_body(response):
        """The API answers with JSON or with a single server-sent event."""
        text = response.text or ""
        try:
            return json.loads(text)
        except ValueError:
            for line in text.splitlines():
                if line.startswith("data:"):
                    try:
                        return json.loads(line[5:].strip())
                    except ValueError:
                        continue
        return None

    def action_delegaize_test_connection(self):
        """Call the read-only ``whoami`` tool of DelegAIze with the API key.

        Nothing from Odoo is sent; the request only proves that address and key work.
        """
        self.ensure_one()
        title = _("DelegAIze connection test")
        base = (self.delegaize_url or DEFAULT_URL).strip().rstrip("/")
        key = (self.delegaize_api_key or "").strip()
        path = "/" + (self.delegaize_api_path or DEFAULT_API_PATH).strip().lstrip("/")
        if not base.lower().startswith(("https://", "http://")):
            return self._delegaize_notify(title, _("The DelegAIze address must start with https://."), "danger")
        if not key:
            return self._delegaize_notify(title, _("Please enter an API key first."), "warning")

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "whoami", "arguments": {}},
        }
        headers = {
            "Authorization": "Bearer %s" % key,
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "User-Agent": "odoo-delegaize-connector/1.0",
        }
        try:
            response = requests.post(base + path, json=payload, headers=headers, timeout=TIMEOUT)
        except requests.exceptions.RequestException as exc:
            _logger.info("DelegAIze connection test failed: %s", exc.__class__.__name__)
            return self._delegaize_notify(
                title, _("DelegAIze is not reachable at %s.", base), "danger")

        body = self._delegaize_parse_body(response)
        error = body.get("error") if isinstance(body, dict) else None
        if response.status_code in (401, 403) or (error and error.get("code") == -32001):
            return self._delegaize_notify(title, _("DelegAIze rejected the API key."), "danger")
        if response.status_code != 200 or not isinstance(body, dict) or error:
            return self._delegaize_notify(
                title,
                _("Unexpected answer from DelegAIze (HTTP %s).", response.status_code),
                "danger")
        result = body.get("result") or {}
        if isinstance(result, dict) and result.get("isError"):
            return self._delegaize_notify(title, _("DelegAIze reported an error for this key."), "danger")
        return self._delegaize_notify(title, _("Connection to DelegAIze works."), "success")
