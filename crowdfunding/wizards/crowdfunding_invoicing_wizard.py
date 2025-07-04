# Copyright 2025 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo import fields, models


class CrowdfundingInvoicingWizard(models.TransientModel):
    _name = "crowdfunding.invoicing.wizard"

    percentage = fields.Float(default=1)

    def action_invoice(self):
        invoices = (
            self.env["crowdfunding.challenge"]
            .browse(
                self.env.context.get("active_ids") or [],
            )
            ._invoice(self.percentage)
        )
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "account.action_move_in_invoice_type",
        )
        action["domain"] = [("id", "in", invoices.ids)]
        return action
