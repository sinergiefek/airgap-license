"""
airgap_license
~~~~~~~~~~~~~~
Zero-Telemetry, Air-Gapped Ed25519 Cryptographic Licensing Engine.
"""

from .core import AirgapKeypair, AirgapLicense, get_machine_fingerprint

__version__ = "0.1.0"
__all__ = ["AirgapKeypair", "AirgapLicense", "get_machine_fingerprint"]
