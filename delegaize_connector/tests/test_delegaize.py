# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse

from odoo.tests import TransactionCase, tagged

REQUESTS_POST = "odoo.addons.delegaize_connector.models.res_config_settings.requests.post"


@tagged("post_install", "-at_install")
class TestDelegaizeConnector(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Muster & Co. GmbH"})
        cls.icp = cls.env["ir.config_parameter"].sudo()

    def _query(self, url):
        parsed = urlparse(url)
        return parsed, {k: v[0] for k, v in parse_qs(parsed.query).items()}

    def test_default_deep_link(self):
        action = self.partner.action_delegaize_open()
        self.assertEqual(action["type"], "ir.actions.act_url")
        self.assertEqual(action["target"], "new")
        parsed, q = self._query(action["url"])
        self.assertEqual(parsed.scheme + "://" + parsed.netloc, "https://delegaize.innov-ai-tive.de")
        self.assertEqual(parsed.path, "/app/open/odoo")
        self.assertEqual(q["source"], "odoo")
        self.assertEqual(q["intent"], "open")
        self.assertEqual(q["model"], "res.partner")
        self.assertEqual(q["id"], str(self.partner.id))
        self.assertEqual(q["db"], self.env.cr.dbname)
        self.assertEqual(q["name"], "Muster & Co. GmbH")

    def test_ask_intent_and_custom_settings(self):
        self.icp.set_param("delegaize_connector.url", "https://example.test/")
        self.icp.set_param("delegaize_connector.link_path", "x/y")
        self.icp.set_param("delegaize_connector.send_record_name", "False")
        parsed, q = self._query(self.partner.action_delegaize_ask()["url"])
        self.assertEqual(parsed.netloc, "example.test")
        self.assertEqual(parsed.path, "/x/y")
        self.assertEqual(q["intent"], "ask")
        self.assertNotIn("name", q)

    def test_home_action(self):
        action = self.env["delegaize.mixin"].action_delegaize_home()
        self.assertEqual(action["url"], "https://delegaize.innov-ai-tive.de/app")

    def test_menu_server_action_runs(self):
        action = self.env.ref("delegaize_connector.action_delegaize_home").run()
        self.assertEqual(action["type"], "ir.actions.act_url")

    def _settings(self, **vals):
        vals.setdefault("delegaize_url", "https://delegaize.innov-ai-tive.de")
        return self.env["res.config.settings"].create(vals)

    def _response(self, status, text):
        resp = MagicMock()
        resp.status_code = status
        resp.text = text
        return resp

    def test_connection_needs_key(self):
        result = self._settings().action_delegaize_test_connection()
        self.assertEqual(result["params"]["type"], "warning")

    def test_connection_ok(self):
        body = '{"jsonrpc":"2.0","id":1,"result":{"content":[{"type":"text","text":"{}"}]}}'
        with patch(REQUESTS_POST, return_value=self._response(200, body)) as post:
            result = self._settings(delegaize_api_key="cpa_test").action_delegaize_test_connection()
        self.assertEqual(result["params"]["type"], "success")
        args, kwargs = post.call_args
        self.assertEqual(args[0], "https://delegaize.innov-ai-tive.de/api/sb/functions/v1/mcp-server")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer cpa_test")
        self.assertEqual(kwargs["json"]["params"]["name"], "whoami")
        # Nothing from Odoo is part of the request.
        self.assertEqual(kwargs["json"]["params"]["arguments"], {})

    def test_connection_event_stream(self):
        body = 'event: message\ndata: {"jsonrpc":"2.0","id":1,"result":{"content":[]}}\n\n'
        with patch(REQUESTS_POST, return_value=self._response(200, body)):
            result = self._settings(delegaize_api_key="cpa_test").action_delegaize_test_connection()
        self.assertEqual(result["params"]["type"], "success")

    def test_connection_rejected_key(self):
        body = '{"jsonrpc":"2.0","id":1,"error":{"code":-32001,"message":"Invalid or expired session"}}'
        with patch(REQUESTS_POST, return_value=self._response(401, body)):
            result = self._settings(delegaize_api_key="cpa_bad").action_delegaize_test_connection()
        self.assertEqual(result["params"]["type"], "danger")
        # "rejected the API key" / "hat den API-Schluessel abgelehnt" (language of the test user)
        self.assertIn("API", result["params"]["message"])

    def test_connection_unreachable(self):
        import requests
        with patch(REQUESTS_POST, side_effect=requests.exceptions.ConnectionError("boom")):
            result = self._settings(delegaize_api_key="cpa_x").action_delegaize_test_connection()
        self.assertEqual(result["params"]["type"], "danger")
