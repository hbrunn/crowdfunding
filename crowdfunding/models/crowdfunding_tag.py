# Copyright 2025 Hunki Enterprises BV
# Copyright 2025 Open Architects Consulting SRL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo import _, api, fields, models


class CrowdfundingTag(models.Model):
    _name = "crowdfunding.tag"
    _description = "Crowdfunding tag"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True, help="Set active to false to hide the Tag without removing it.")
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
