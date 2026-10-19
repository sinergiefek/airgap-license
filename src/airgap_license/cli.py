"""
airgap_license.cli
~~~~~~~~~~~~~~~~~~
Command-line interface for generating keypairs, issuing tokens, and verifying licenses offline.
"""

import argparse
import json
import sys

from .core import AirgapKeypair, AirgapLicense, get_machine_fingerprint


def main():
    parser = argparse.ArgumentParser(
        prog="airgap-license",
        description="Zero-Telemetry, Air-Gapped Ed25519 Cryptographic Licensing Engine",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Keygen command
    subparsers.add_parser("keygen", help="Generate a new Ed25519 public/private keypair")

    # Fingerprint command
    subparsers.add_parser("fingerprint", help="Display local machine hardware fingerprint")

    # Issue command
    issue_p = subparsers.add_parser("issue", help="Issue a signed license token")
    issue_p.add_argument("--customer", required=True, help="Customer or organization name")
    issue_p.add_argument("--plan", default="enterprise", help="Subscription or tier plan (default: enterprise)")
    issue_p.add_argument("--features", default="core", help="Comma-separated list of enabled features")
    issue_p.add_argument("--expires", default=None, help="Expiration date in ISO format (e.g. 2027-12-31T23:59:59Z), or empty for lifetime")
    issue_p.add_argument("--privkey", required=True, help="Private key in hex format")
    issue_p.add_argument("--lock-machine", default=None, help="Machine fingerprint to lock license to")

    # Verify command
    verify_p = subparsers.add_parser("verify", help="Verify a license token offline")
    verify_p.add_argument("token", help="Base64 license token string")
    verify_p.add_argument("--pubkey", required=True, help="Public key in hex format")
    verify_p.add_argument("--check-machine", action="store_true", help="Enforce machine fingerprint matching")

    args = parser.parse_args()

    if args.command == "keygen":
        priv, pub = AirgapKeypair.generate()
        print("=== Generated Ed25519 Keypair ===")
        print(f"Private Key (KEEP SECRET): {priv}")
        print(f"Public Key (EMBED IN APP): {pub}")

    elif args.command == "fingerprint":
        fp = get_machine_fingerprint()
        print(f"Machine Fingerprint: {fp}")

    elif args.command == "issue":
        feature_list = [f.strip() for f in args.features.split(",") if f.strip()]
        token = AirgapLicense.issue(
            customer=args.customer,
            plan=args.plan,
            features=feature_list,
            expires_at=args.expires,
            private_key_hex=args.privkey,
            machine_lock=args.lock_machine,
        )
        print("=== Signed License Token ===")
        print(token)

    elif args.command == "verify":
        valid, err, payload = AirgapLicense.verify(
            token=args.token,
            public_key_hex=args.pubkey,
            check_machine_lock=args.check_machine,
        )
        if valid:
            print("[VALID] Cryptographic signature matches. License is authentic!")
            print(json.dumps(payload, indent=2))
            sys.exit(0)
        else:
            print(f"[INVALID] Verification failed: {err}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
