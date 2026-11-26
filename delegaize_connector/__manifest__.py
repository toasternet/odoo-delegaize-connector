# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).
{
    "name": "DelegAIze Connector",
    "summary": "Open Odoo contacts, leads, quotations and invoices in DelegAIze "
               "and hand them to an AI agent - only when a user clicks.",
    "version": "17.0.1.0.0",
    "category": "Productivity",
    "author": "Innov-AI-tive",
    "website": "https://delegaize.innov-ai-tive.de/branchen/backoffice?utm_source=odoo_apps&utm_medium=marketplace&utm_campaign=odoo_connector_202611&ref=th",
    "support": "info@innov-ai-tive.de",
    "license": "LGPL-3",
    "depends": ["base_setup"],
    "external_dependencies": {"python": ["requests"]},
    "data": [
        "data/delegaize_data.xml",
        "views/res_config_settings_views.xml",
        "views/res_partner_views.xml",
        "views/delegaize_menus.xml",
    ],
    "images": ["static/description/banner.png"],
    "installable": True,
    "application": True,
}
