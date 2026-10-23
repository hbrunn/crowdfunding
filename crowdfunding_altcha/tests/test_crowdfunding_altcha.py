import odoo.tests
from odoo.tools.misc import mute_logger


@odoo.tests.tagged("-at_install", "post_install")
class TestCrowdfundingAltcha(odoo.tests.HttpCase):
    def test_altcha(self):
        """
        Test that submitting to the payment controller without altcha is blocked
        """
        challenge = self.env.ref("crowdfunding.demo_challenge")
        with (
            mute_logger("odoo.addons.website_altcha.models.ir_http"),
            mute_logger("odoo.http"),
        ):
            result = self.url_open(f"{challenge.website_url}/pay?name=test")
        self.assertEqual(result.status_code, 400)
        self.assertIn("Suspicious activity detected by Altcha", result.text)
