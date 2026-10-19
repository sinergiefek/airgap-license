<div align="center">

# 🔑 Airgap-License
### **Zero-Telemetry, Air-Gapped Ed25519 Cryptographic Licensing Engine**
*Mathematically Verifiable, Asymmetric Software Licensing for Sovereign B2B & On-Premise Deployments.*

[![License: MIT](https://img.shields.io/badge/License-MIT-0B1220?style=for-the-badge&logoColor=white)](LICENSE)
[![Crypto: Ed25519](https://img.shields.io/badge/Crypto-Ed25519_Asymmetric-0B1220?style=for-the-badge&logo=shield&logoColor=38BDF8)](https://ed25519.cr.yp.to/)
[![Privacy: Zero Telemetry](https://img.shields.io/badge/Telemetry-Zero_%28Air--Gapped%29-0B1220?style=for-the-badge&logoColor=10B981)](README.md)
[![Architecture: PSTACK](https://img.shields.io/badge/PSTACK-Mandate_18_Compliant-0B1220?style=for-the-badge&logoColor=F59E0B)](https://github.com/sinergiefek)

---

> *"Enterprise clients in banking, defense, and high-security sectors refuse to allow on-premise software to 'phone home' to external licensing servers. Airgap-License provides 100% offline, mathematical proof of entitlement."*

</div>

---

### 💡 The Problem with Traditional Licensing

Traditional software licensing tools (Keygen.sh, Stripe Billing, Cryptlex) require constant HTTP heartbeats:
* ❌ **Air-Gapped & High-Security Rejection:** Defense, healthcare, and financial intranets block outbound internet traffic. Phone-home licensing fails immediately.
* ❌ **Vendor Dependency:** If your licensing SaaS experiences downtime or rate limits, your client's production software crashes.
* ❌ **Symmetric Secrets Leakage:** Using simple hash keys or symmetric secrets means embedding the secret inside your binary, making reverse engineering trivial.

**Airgap-License solves this with Asymmetric Elliptic-Curve Cryptography (Ed25519):**
* ✅ **Zero-Telemetry (100% Offline):** Verification happens strictly on the local CPU in microseconds with zero network calls.
* ✅ **Public-Key Only in Client:** Only the 32-byte Ed25519 Public Key is embedded in the distributed app. The Private Signing Key never leaves your secure build environment.
* ✅ **Tamper-Evident:** Any modification to customer name, allowed features, or expiration date breaks the cryptographic signature.
* ✅ **Optional Node/Hardware Lock:** Enforces machine fingerprint binding (MAC + Hostname SHA-256) to prevent unauthorized container cloning.

---

### 📐 Architectural Flow

```
┌────────────────────────────────────────────────────────────────────────┐
│                        VENDOR SECURE ENVIRONMENT                       │
│  [Private Key (Secret)] ──> AirgapLicense.issue(...) ──> [Signed Token] │
│                                                                  │     │
└──────────────────────────────────────────────────────────────────┼─────┘
                                                                   │ (Delivered via Email / Portal)
┌──────────────────────────────────────────────────────────────────▼─────┐
│                   AIR-GAPPED CLIENT ON-PREMISE NODE                    │
│  [Embedded Public Key] ──> AirgapLicense.verify(token)                 │
│                                  │                                     │
│            ┌─────────────────────┴─────────────────────┐               │
│            ▼                                           ▼               │
│   [Signature Valid & Unexpired]             [Tampered or Expired]      │
│      ==> UNLOCK FEATURES                       ==> HALT EXECUTION      │
└────────────────────────────────────────────────────────────────────────┘
```

---

### 🚀 Quickstart

#### 1. Generate Keypair (One-Time Vendor Setup)

```bash
airgap-license keygen
```
Outputs:
* **Private Key:** Store securely in your CI/CD vault.
* **Public Key:** Embed this directly in your Python/Go/Node.js application.

#### 2. Issue a Signed License Token

```bash
airgap-license issue \
  --customer "Acme Corporation" \
  --plan "enterprise" \
  --features "multi_tenant,saml_sso,audit_log" \
  --expires "2028-12-31T23:59:59Z" \
  --privkey "<YOUR_HEX_PRIVATE_KEY>"
```

#### 3. Verify Offline in Client Application

```python
from airgap_license import AirgapLicense

# The public key safe to bundle inside your application
PUBLIC_KEY = "3a8f...b24c"

license_token = "eyJjdXN0b21lci...b64_payload.sig_b64"

is_valid, error, payload = AirgapLicense.verify(license_token, PUBLIC_KEY)

if is_valid:
    print(f"✅ License authentic for {payload['customer']} (Plan: {payload['plan']})")
    if "saml_sso" in payload["features"]:
        enable_saml_sso()
else:
    raise SystemExit(f"🚨 LICENSE FAILURE: {error}")
```

---

### 🏢 Open Core vs Enterprise Licensing

| Capability | Community (MIT) | Enterprise License Server |
| :--- | :---: | :---: |
| Ed25519 Asymmetric Verification | ✅ | ✅ |
| Feature Gating & Expiration Checks | ✅ | ✅ |
| Machine Fingerprint Node Locking | ✅ | ✅ |
| Standalone CLI Tool | ✅ | ✅ |
| **Automated Stripe / Xendit Webhook Token Generator** | ❌ | 👑 **Enterprise** |
| **Whitelabel Self-Service Customer License Portal** | ❌ | 👑 **Enterprise** |
| **Polyglot SDKs (C / Rust FFI, Go, PHP, Java)** | ❌ | 👑 **Enterprise** |
| **TPM 2.0 / Hardware Security Module (HSM) Binding** | ❌ | 👑 **Enterprise** |

For Enterprise licensing systems, air-gapped activation portals, or IP asset audits, visit [Sinergi Mitra Visitama](https://sinergimitravisitama.my.id).

---

### 📄 License

Licensed under the permissive [MIT License](LICENSE).  
Copyright (c) 2026 Setijono (Sinergi Mitra Visitama).
