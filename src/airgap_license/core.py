"""
airgap_license.core
~~~~~~~~~~~~~~~~~~~
Zero-Telemetry, Air-Gapped Ed25519 Cryptographic Licensing Engine.
Verifies asymmetric signatures offline with zero phone-home requirement.
"""

import base64
import datetime
import hashlib
import json
import socket
import uuid
from typing import Any, Dict, List, Optional, Tuple

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519


def canonical_json_bytes(data: Dict[str, Any]) -> bytes:
    """Produces deterministic canonical JSON bytes with sorted keys."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def get_machine_fingerprint() -> str:
    """
    Generates a deterministic machine fingerprint based on node MAC and hostname.
    Useful for hardware-locked on-premise node licensing.
    """
    node = uuid.getnode()
    host = socket.gethostname()
    preimage = f"{node}:{host}".encode("utf-8")
    return hashlib.sha256(preimage).hexdigest()[:32]


class AirgapKeypair:
    """Generates and serializes Ed25519 asymmetric keypairs."""

    @staticmethod
    def generate() -> Tuple[str, str]:
        """
        Generates a new Ed25519 keypair.
        Returns (private_key_hex, public_key_hex).
        """
        priv = ed25519.Ed25519PrivateKey.generate()
        pub = priv.public_key()

        priv_bytes = priv.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )
        pub_bytes = pub.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )

        return priv_bytes.hex(), pub_bytes.hex()


class AirgapLicense:
    """Signs and verifies cryptographic air-gapped software licenses."""

    @staticmethod
    def issue(
        customer: str,
        plan: str,
        features: List[str],
        expires_at: Optional[str],  # ISO format string or None for lifetime
        private_key_hex: str,
        machine_lock: Optional[str] = None,
        custom_metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Issues an offline-verifiable license token.
        Token is encoded as base64(canonical_json(payload)) + "." + base64(signature).
        """
        priv_bytes = bytes.fromhex(private_key_hex)
        priv_key = ed25519.Ed25519PrivateKey.from_private_bytes(priv_bytes)

        payload: Dict[str, Any] = {
            "license_id": str(uuid.uuid4()),
            "customer": customer,
            "plan": plan,
            "features": sorted(features),
            "issued_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "expires_at": expires_at,
            "machine_lock": machine_lock,
            "metadata": custom_metadata or {},
        }

        payload_bytes = canonical_json_bytes(payload)
        sig = priv_key.sign(payload_bytes)

        payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode("ascii")
        sig_b64 = base64.urlsafe_b64encode(sig).decode("ascii")

        return f"{payload_b64}.{sig_b64}"

    @staticmethod
    def verify(
        token: str,
        public_key_hex: str,
        check_machine_lock: bool = False,
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Verifies a license token completely offline using the public key.
        Returns (is_valid, error_message, payload_dict).
        """
        parts = token.strip().split(".")
        if len(parts) != 2:
            return False, "Malformed license token format", None

        payload_b64, sig_b64 = parts[0], parts[1]

        try:
            payload_bytes = base64.urlsafe_b64decode(payload_b64.encode("ascii"))
            sig_bytes = base64.urlsafe_b64decode(sig_b64.encode("ascii"))
        except Exception as e:
            return False, f"Failed to decode base64 token: {e}", None

        # Verify Ed25519 signature
        try:
            pub_bytes = bytes.fromhex(public_key_hex)
            pub_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)
            pub_key.verify(sig_bytes, payload_bytes)
        except InvalidSignature:
            return False, "Cryptographic signature mismatch! License has been tampered with or forged.", None
        except Exception as e:
            return False, f"Signature verification error: {e}", None

        # Parse payload
        try:
            payload = json.loads(payload_bytes.decode("utf-8"))
        except Exception as e:
            return False, f"Invalid JSON payload in license: {e}", None

        # Check expiration date
        expires_at = payload.get("expires_at")
        if expires_at:
            try:
                exp_dt = datetime.datetime.fromisoformat(expires_at)
                now_dt = datetime.datetime.now(datetime.timezone.utc)
                if now_dt > exp_dt:
                    return False, f"License expired on {expires_at}", payload
            except ValueError:
                return False, f"Invalid expires_at format: {expires_at}", payload

        # Check machine hardware lock if required
        if check_machine_lock and payload.get("machine_lock"):
            current_fp = get_machine_fingerprint()
            if payload["machine_lock"] != current_fp:
                return (
                    False,
                    f"Machine fingerprint mismatch! Required: {payload['machine_lock']}, Current: {current_fp}",
                    payload,
                )

        return True, None, payload
