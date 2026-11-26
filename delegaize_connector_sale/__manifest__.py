# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).
{
    "name": "DelegAIze Connector - Sales",
    "summary": "Adds the DelegAIze buttons to quotations and sales orders. Installed automatically "
               "together with DelegAIze Connector and Sales.",
    "version": "17.0.1.0.0",
    "category": "Hidden",
    "author": "Innov-AI-tive",
    "website": "https://delegaize.innov-ai-tive.de/branchen/backoffice?utm_source=odoo_apps&utm_medium=marketplace&utm_campaign=odoo_connector_202611&ref=th",
    "support": "info@innov-ai-tive.de",
    "license": "LGPL-3",
    "depends": ["delegaize_connector", "sale"],
    "data": ["views/sale_order_views.xml"],
    "installable": True,
    "auto_install": True,
}
