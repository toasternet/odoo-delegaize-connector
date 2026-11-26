# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).
from urllib.parse import parse_qs, urlparse

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestDelegaizeLink(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.record = cls.env["account.move"].create({"move_type": "out_invoice", "partner_id": cls.env["res.partner"].create({"name": "Kunde"}).id})

    def test_link_points_to_record(self):
        for method, intent in (("action_delegaize_open", "open"), ("action_delegaize_ask", "ask")):
            url = getattr(self.record, method)()["url"]
            q = {k: v[0] for k, v in parse_qs(urlparse(url).query).items()}
            self.assertEqual(q["model"], "account.move")
            self.assertEqual(q["id"], str(self.record.id))
            self.assertEqual(q["intent"], intent)
