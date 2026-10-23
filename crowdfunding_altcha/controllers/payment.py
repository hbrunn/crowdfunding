# Copyright 2025 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)


from odoo import http

from odoo.addons.crowdfunding.controllers import payment as crowdfunding_payment


class Payment(crowdfunding_payment.Payment):
    def _crowdfunding_create_partner(self, challenge, values):
        if values:
            http.request.env["ir.http"]._verify_request_recaptcha_token("crowdfunding")
        return super()._crowdfunding_create_partner(challenge, values)
