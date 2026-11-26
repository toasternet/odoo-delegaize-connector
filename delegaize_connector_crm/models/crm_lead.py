# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).
from odoo import models


class CrmLead(models.Model):
    _name = "crm.lead"
    _inherit = ["crm.lead", "delegaize.mixin"]
