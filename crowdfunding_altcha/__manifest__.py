# Copyright 2026 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

{
    "name": "Crowdfunding: ALTCHA support",
    "summary": "Protect pledges with ALTCHA",
    "version": "18.0.1.0.0",
    "development_status": "Alpha",
    "category": "Crowdfunding",
    "website": "https://github.com/OCA/crowdfunding",
    "author": "Hunki Enterprises BV, Odoo Community Association (OCA)",
    "maintainers": ["hbrunn"],
    "license": "AGPL-3",
    "depends": [
        "crowdfunding",
        "website_altcha",
    ],
    "data": [
        "templates/payment.xml",
    ],
    "demo": [
        "demo/res_company.xml",
    ],
    "assets": {
        "web.assets_tests": [
            "crowdfunding_altcha/static/tests/tours/crowdfunding_frontend.esm.js",
        ],
    },
    "auto_install": True,
}
