# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).
"""Deep links from Odoo records into DelegAIze.

Nothing in this module sends record data to DelegAIze on its own. A link is
only built when a user clicks a button, and the browser of that user opens it.
The link carries a reference (database, model, id) and - if enabled in the
settings - the display name, so DelegAIze can find or match the record.
"""
from urllib.parse import urlencode

from odoo import _, api, models
from odoo.exceptions import UserError

DEFAULT_URL = "https://delegaize.innov-ai-tive.de"
DEFAULT_LINK_PATH = "/app/open/odoo"
DEFAULT_API_PATH = "/api/sb/functions/v1/mcp-server"

PARAM_URL = "delegaize_connector.url"
PARAM_LINK_PATH = "delegaize_connector.link_path"
PARAM_SEND_NAME = "delegaize_connector.send_record_name"


class DelegaizeMixin(models.AbstractModel):
    _name = "delegaize.mixin"
    _description = "DelegAIze deep link helper"

    # ------------------------------------------------------------------
    # configuration
    # ------------------------------------------------------------------
    @api.model
    def _delegaize_base_url(self):
        icp = self.env["ir.config_parameter"].sudo()
        url = (icp.get_param(PARAM_URL) or DEFAULT_URL).strip()
        if not url.lower().startswith(("https://", "http://")):
            raise UserError(_("The DelegAIze address must start with https://."))
        return url.rstrip("/")

    @api.model
    def _delegaize_link_path(self):
        icp = self.env["ir.config_parameter"].sudo()
        path = (icp.get_param(PARAM_LINK_PATH) or DEFAULT_LINK_PATH).strip()
        return "/" + path.lstrip("/")

    @api.model
    def _delegaize_send_name(self):
        icp = self.env["ir.config_parameter"].sudo()
        value = icp.get_param(PARAM_SEND_NAME, "True")
        return str(value).lower() not in ("false", "0", "")

    # ------------------------------------------------------------------
    # link building
    # ------------------------------------------------------------------
    def _delegaize_record_params(self, intent):
        self.ensure_one()
        icp = self.env["ir.config_parameter"].sudo()
        params = {
            "source": "odoo",
            "intent": intent,
            "instance": (icp.get_param("web.base.url") or "").rstrip("/"),
            "db": self.env.cr.dbname,
            "model": self._name,
            "id": self.id,
        }
        if self._delegaize_send_name():
            params["name"] = self.display_name or ""
        return params

    def _delegaize_record_url(self, intent="open"):
        self.ensure_one()
        if intent not in ("open", "ask"):
            raise UserError(_("Unknown DelegAIze action."))
        query = urlencode(self._delegaize_record_params(intent))
        return "%s%s?%s" % (self._delegaize_base_url(), self._delegaize_link_path(), query)

    @api.model
    def _delegaize_url_action(self, url):
        return {"type": "ir.actions.act_url", "url": url, "target": "new"}

    # ------------------------------------------------------------------
    # button actions (called from form views)
    # ------------------------------------------------------------------
    def action_delegaize_open(self):
        self.ensure_one()
        return self._delegaize_url_action(self._delegaize_record_url("open"))

    def action_delegaize_ask(self):
        self.ensure_one()
        return self._delegaize_url_action(self._delegaize_record_url("ask"))

    @api.model
    def action_delegaize_home(self):
        """Target of the top-level "DelegAIze" menu."""
        return self._delegaize_url_action(self._delegaize_base_url() + "/app")
