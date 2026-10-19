"""
Unit tests for airgap_license engine.
Tests offline Ed25519 cryptographic validation, tampering detection, and expiration guards.
"""

import datetime
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from airgap_license.core import AirgapKeypair, AirgapLicense, get_machine_fingerprint


class TestAirgapLicense(unittest.TestCase):

    def setUp(self):
        self.priv_hex, self.pub_hex = AirgapKeypair.generate()

    def test_valid_license_verification(self):
        token = AirgapLicense.issue(
            customer="Acme Corp",
            plan="enterprise",
            features=["multi_tenant", "sso", "audit_log"],
            expires_at="2099-01-01T00:00:00Z",
            private_key_hex=self.priv_hex,
        )

        valid, err, payload = AirgapLicense.verify(token, self.pub_hex)
        self.assertTrue(valid)
        self.assertIsNone(err)
        self.assertEqual(payload["customer"], "Acme Corp")
        self.assertEqual(payload["plan"], "enterprise")
        self.assertIn("sso", payload["features"])

    def test_tampered_payload_fails(self):
        token = AirgapLicense.issue(
            customer="Normal Client",
            plan="starter",
            features=["basic"],
            expires_at="2099-01-01T00:00:00Z",
            private_key_hex=self.priv_hex,
        )

        # Tamper with the token: replace payload base64 part
        parts = token.split(".")
        tampered_token = "eyJjdXN0b21lciI6ICJNZWdhIENvcnAiLCAicGxhbiI6ICJlbnRlcnByaXNlIn0=." + parts[1]

        valid, err, payload = AirgapLicense.verify(tampered_token, self.pub_hex)
        self.assertFalse(valid)
        self.assertIn("Cryptographic signature mismatch", err)

    def test_expired_license_fails(self):
        past_date = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)).isoformat()
        token = AirgapLicense.issue(
            customer="Expired Corp",
            plan="trial",
            features=["core"],
            expires_at=past_date,
            private_key_hex=self.priv_hex,
        )

        valid, err, payload = AirgapLicense.verify(token, self.pub_hex)
        self.assertFalse(valid)
        self.assertIn("License expired", err)

    def test_machine_lock(self):
        current_fp = get_machine_fingerprint()
        token = AirgapLicense.issue(
            customer="Locked Node",
            plan="onprem",
            features=["core"],
            expires_at=None,
            private_key_hex=self.priv_hex,
            machine_lock=current_fp,
        )

        # Verify on matching machine
        valid, err, _ = AirgapLicense.verify(token, self.pub_hex, check_machine_lock=True)
        self.assertTrue(valid)

        # Token with different machine fingerprint
        token_wrong_machine = AirgapLicense.issue(
            customer="Locked Node",
            plan="onprem",
            features=["core"],
            expires_at=None,
            private_key_hex=self.priv_hex,
            machine_lock="foreign_machine_deadbeef1234",
        )
        valid, err, _ = AirgapLicense.verify(token_wrong_machine, self.pub_hex, check_machine_lock=True)
        self.assertFalse(valid)
        self.assertIn("Machine fingerprint mismatch", err)


if __name__ == "__main__":
    unittest.main()
