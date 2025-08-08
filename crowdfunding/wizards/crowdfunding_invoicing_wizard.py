# Copyright 2025 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo import api, fields, models


class CrowdfundingInvoicingWizard(models.TransientModel):
    _name = "crowdfunding.invoicing.wizard"

    percentage = fields.Float(default=1)
    challenge_ids = fields.Many2many("crowdfunding.challenge")
    vendor_bill_ids = fields.One2many(
        related="challenge_ids.vendor_bill_ids", string="Existing vendor bills"
    )

    def default_get(self, fields_list):
        result = super().default_get(fields_list)
        if "challenge_ids" in fields_list and "challenge_ids" not in result:
            result["challenge_ids"] = [(6, 0, self.env.context.get("active_ids"))]
        return result

    def action_invoice(self):
        invoices = self.challenge_ids._in_invoice(self.percentage)
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "account.action_move_in_invoice_type",
        )
        action["domain"] = [("id", "in", invoices.ids)]
        return action

    @api.onchange("vendor_bill_ids")
    def _onchange_vendor_bill_ids(self):
        if self.vendor_bill_ids:
            self.percentage = 0
