# Copyright 2025 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo import _, api, exceptions, fields, models, tools

from odoo.addons.http_routing.models.ir_http import slug


class CrowdfundingChallenge(models.Model):
    _name = "crowdfunding.challenge"
    _description = "Crowdfunding challenge"
    _inherit = ["mail.thread", "website.published.mixin", "website.seo.metadata"]
    _mail_post_access = "read"
    _mail_flat_thread = False

    name = fields.Char(required=True, tracking=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("open", "Open"),
            ("claimed", "Claimed"),
            ("submitted", "Submitted"),
            ("done", "Done"),
        ],
        default="draft",
        tracking=True,
    )
    description = fields.Html()
    description_url = fields.Char()
    description_image = fields.Binary()
    claimed_partner_id = fields.Many2one(
        "res.partner", string="Claimed by partner", tracking=True
    )
    target_amount = fields.Monetary(tracking=True)
    fee_amount = fields.Monetary(compute="_compute_amounts", store=True, readonly=True)
    fee_percentage = fields.Float(default=lambda self: self._default_fee_percentage())
    claimed_partner_amount = fields.Monetary(
        compute="_compute_amounts", store=True, readonly=True
    )
    funding_state = fields.Selection(
        [
            ("needs_funding", "Needs funding"),
            ("funded", "Funded"),
        ],
        compute="_compute_funding_state",
        store=True,
        readonly=True,
        tracking=True,
    )
    pledged_percentage = fields.Float(
        compute="_compute_funding_state", readonly=True, store=True, tracking=True
    )
    pledged_amount = fields.Monetary(
        compute="_compute_transactions",
        readonly=True,
        store=True,
        tracking=True,
    )
    transaction_count = fields.Integer(compute="_compute_transactions", store=True)
    transaction_ids = fields.One2many(
        "payment.transaction", "crowdfunding_challenge_id"
    )
    vendor_bill_ids = fields.One2many(
        "account.move",
        "crowdfunding_challenge_id",
        domain=[("move_type", "=", "in_invoice")],
    )
    currency_id = fields.Many2one(related="company_id.currency_id")
    website_meta_title = fields.Char(related="name")
    website_meta_description = fields.Text(compute="_compute_website_meta_description")
    website_meta_og_img = fields.Char(compute="_compute_website_meta_og_img")
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    def _default_fee_percentage(self):
        company = (
            self.env["res.company"].browse(
                self.default_get(["company_id"]).get("company_id") or []
            )
            or self.env.user.company
        )
        return company.crowdfunding_default_fee_percentage

    @api.depends("fee_percentage", "target_amount")
    def _compute_amounts(self):
        for this in self:
            this.fee_amount = this.currency_id.round(
                this.target_amount * this.fee_percentage
            )
            this.claimed_partner_amount = this.target_amount - this.fee_amount

    @api.depends("pledged_amount", "target_amount")
    def _compute_funding_state(self):
        for this in self:
            this.pledged_percentage = (
                this.target_amount
                and (this.pledged_amount / this.target_amount * 100)
                or 0
            )
            this.funding_state = (
                "needs_funding" if this.pledged_percentage < 100 else "funded"
            )

    @api.depends("transaction_ids.amount", "transaction_ids.state")
    def _compute_transactions(self):
        for this in self:
            this.transaction_count = len(this.transaction_ids)
            this.pledged_amount = sum(
                this.transaction_ids.filtered(lambda x: x.state == "done").mapped(
                    "amount"
                )
            )

    def _compute_website_url(self):
        for this in self:
            this.website_url = f"/crowdfunding/{slug(this)}"

    def _compute_website_meta_description(self):
        for this in self:
            this.website_meta_description = tools.html2plaintext(this.description)

    def _compute_website_meta_og_img(self):
        for this in self:
            this.website_meta_og_img = (
                f"/web/image/crowdfunding.challenge/{slug(this)}/description_image"
                if this.description_image
                else None
            )

    def action_open(self):
        self.filtered(lambda x: x.state == "draft").write(
            {"state": "open", "is_published": True}
        )

    def action_claimed(self):
        self.write({"state": "claimed"})

    def action_submitted(self):
        self.write({"state": "submitted"})

    def action_done(self):
        for this in self:
            if (
                this.currency_id.compare_amounts(
                    sum(
                        this.vendor_bill_ids.filtered(
                            lambda x: x.payment_state == "paid"
                        ).mapped("amount_total")
                    ),
                    this.claimed_partner_amount,
                )
                != 0
            ):
                raise exceptions.UserError(
                    _(
                        "Challenge %(name)s cannot be marked as done as the amount "
                        "paid differs from the amount to be paid"
                    )
                    % this
                )
        self.write({"state": "done"})

    def action_cancel(self):
        self.write(
            {"state": "draft", "is_published": False, "claimed_partner_id": False}
        )

    def action_payment_transactions(self):
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "payment.action_payment_transaction"
        )
        return dict(action, domain=[("crowdfunding_challenge_id", "in", self.ids)])

    def action_vendor_bills(self):
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "account.action_move_in_invoice_type",
        )
        return dict(action, domain=[("crowdfunding_challenge_id", "in", self.ids)])

    def action_invoice_wizard(self):
        return self.env["ir.actions.act_window"]._for_xml_id(
            "crowdfunding.action_crowdfunding_invoicing_wizard"
        )

    def _invoice(self, percentage=None, **kwargs):
        AccountMove = self.env["account.move"]
        invoices = AccountMove.browse([])
        for this in self:
            invoices += AccountMove.create(this._invoice_vals(percentage, **kwargs))
        return invoices

    def _invoice_vals(self, percentage=None, **kwargs):
        self.ensure_one()
        invoice_vals = self.env["account.move"].play_onchanges(
            {
                "move_type": "in_invoice",
                "ref": self.name,
                "crowdfunding_challenge_id": self.id,
                "partner_id": self.claimed_partner_id.id,
            },
            ["partner_id"],
        )
        invoice_line_vals = self.env["account.move.line"].play_onchanges(
            {
                "move_id": self.env["account.move"].new(invoice_vals),
                "product_id": self.company_id.crowdfunding_product_id.id,
            },
            ["product_id"],
        )
        invoice_line_vals["price_unit"] = self.claimed_partner_amount * (
            percentage or 1
        )
        return dict(
            invoice_vals,
            invoice_line_ids=[(0, 0, invoice_line_vals)],
        )

    def _domain_portal_access(self):
        return [("is_published", "=", True)]

    def _domain_website_access(self):
        return [("is_published", "=", True)]

    def _claim(self, partner=None):
        partner = partner or self.env.user.partner_id
        can_claim = self.filtered(lambda x: x._can_claim(partner))
        can_claim.write(
            {
                "claimed_partner_id": partner.id,
            }
        )
        can_claim.action_claimed()

    def _can_claim(self, partner=None):
        self.ensure_one()
        return not self.claimed_partner_id and self.state == "open"

    def _can_pay(self, partner=None):
        self.ensure_one()
        return self.state in ("open", "claimed")
