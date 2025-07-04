# Copyright 2025 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

import uuid
from contextlib import contextmanager

import werkzeug

from odoo import _, http
from odoo.http import request

from odoo.addons.payment.controllers.portal import PaymentProcessing, WebsitePayment


class Payment(WebsitePayment):
    @http.route()
    def transaction(self, *args, **kwargs):
        with self._crowdfunding_update_transaction(kwargs):
            return super().transaction(*args, **kwargs)

    @http.route()
    def payment_token(self, *args, **kwargs):
        with self._crowdfunding_update_transaction(kwargs):
            return super().payment_token(*args, **kwargs)

    @contextmanager
    def _crowdfunding_update_transaction(self, kwargs):
        transactions_before = set(PaymentProcessing.get_payment_transaction_ids())
        yield
        transactions = (
            request.env["payment.transaction"]
            .browse(
                set(PaymentProcessing.get_payment_transaction_ids())
                - transactions_before
            )
            .sudo()
        )
        challenge_id = request.httprequest.args.get(
            "crowdfunding_challenge_id"
        ) or kwargs.get("crowdfunding_challenge_id")
        if challenge_id:
            transactions.filtered(
                lambda x: not ("sale_order_ids" in x._fields and x.sale_order_ids)
                and not x.invoice_ids
            ).write({"crowdfunding_challenge_id": int(challenge_id)})

    def _crowdfunding_get_partner(self):
        return (
            not request.env.user._is_public()
            and request.env.user.partner_id
            or request.env["res.partner"].browse(
                request.session.get("crowdfunding", {}).get("partner_id", [])
            )
        )

    def _crowdfunding_create_partner_mandatory_fields(self, challenge):
        return ("name", "email", "street", "city", "country_id")

    def _crowdfunding_create_partner_optional_fields(self, challenge):
        return ()

    def _crowdfunding_create_partner_get_errors(self, challenge, values):
        errors = {}
        for key in self._crowdfunding_create_partner_mandatory_fields(challenge):
            if not values.get(key):
                errors[key] = _("Required field")
        if (
            not str(values.get("country_id")).isdigit()
            or not request.env["res.country"].browse(int(values["country_id"])).exists()
        ):
            errors["country_id"] = _("Invalid country")
        return errors

    def _crowdfunding_create_partner_get_values(self, challenge, values):
        result = {
            key: values[key]
            for key in (
                self._crowdfunding_create_partner_mandatory_fields(challenge)
                + self._crowdfunding_create_partner_optional_fields(challenge)
            )
            if key in values
        }
        result["country_id"] = int(result["country_id"])
        return result

    def _crowdfunding_create_partner(self, challenge, values):
        Partner = request.env["res.partner"]
        if self._crowdfunding_create_partner_get_errors(challenge, values):
            return Partner
        partner = Partner.sudo().create(
            self._crowdfunding_create_partner_get_values(challenge, values)
        )
        request.session.setdefault("crowdfunding", {})["partner_id"] = partner.id
        return partner

    @http.route(
        ["/crowdfunding/<model('crowdfunding.challenge'):challenge>/pay"],
        type="http",
        auth="public",
        website=True,
        sitemap=False,
    )
    def crowdfunding_pay(self, challenge, **kwargs):
        if not challenge._can_pay(request.env.user.partner_id):
            raise werkzeug.exceptions.NotFound()

        partner = self._crowdfunding_get_partner() or self._crowdfunding_create_partner(
            challenge, kwargs
        )
        if not partner:
            return request.render(
                "crowdfunding.pay_partner_details",
                {
                    "object": challenge,
                    "form_values": kwargs,
                    "form_errors": kwargs
                    and self._crowdfunding_create_partner_get_errors(challenge, kwargs)
                    or {},
                },
            )
        elif "amount" not in kwargs:
            result = request.render("crowdfunding.pay_details", {"object": challenge})
        else:
            kwargs["amount"] = abs(float(kwargs["amount"]))
            kwargs["reference"] = "crowdfunding-%s-%s" % (
                challenge.id,
                uuid.uuid4(),
            )

            payment_wizard = request.env["payment.link.wizard"].new(
                {
                    "partner_id": partner.id,
                    "currency_id": challenge.currency_id.id,
                    "amount": kwargs["amount"],
                    "res_model": challenge._name,
                    "res_id": challenge.id,
                }
            )
            payment_wizard._compute_values()
            kwargs["access_token"] = payment_wizard.access_token
            kwargs["partner_id"] = partner.id

            kwargs["currency_id"] = challenge.currency_id.id
            result = self.pay(**kwargs)
            result.template = "crowdfunding.pay"
            result.qcontext["crowdfunding_challenge"] = challenge
        return result
