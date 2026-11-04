# Authentication, MFA, SSH and WireGuard key lifecycle

## Account security

Quantum Platform's Django backend uses Django Allauth and associated MFA/account flows. Protect email verification, login, password resets and MFA enrollment as account-security operations; the authenticated Astro app is a client, not the trust anchor. Admin and API endpoints must enforce permissions server-side. A session cookie or CSRF token is not an ACP signing key, and its presence in browser storage should never be used as HPC identity proof.

Use account security pages to configure available MFA authenticators, manage recovery and revoke sessions through supported controls. Password reset and MFA recovery should use the official account flow, not a support agent requesting recovery codes.

## SSH key registration

Generate key material on a trusted local device and keep **private** key material there. Only register the public key:

```sh
ssh-keygen -t ed25519 -a 100 -f ~/.ssh/id_ed25519_research
cat ~/.ssh/id_ed25519_research.pub
```

Do not automatically overwrite an existing key: choose a distinct filename, verify permissions and backup/recovery according to your local policy. The portal validates and records supported SSH public key types. Registration is not automatic shell entitlement; an approved identity and provisioning/reconciliation must also exist. Rotate compromised keys promptly and revoke old entries.

## WireGuard public keys

WireGuard is a private network access mechanism. Generate device keys using the approved client procedure; send **only the public key** to the portal. The private key should not appear in a browser, wiki, shell history, screenshot, issue or model chat. A portal-issued client configuration must be handled as sensitive because it can include device-specific information. Infrastructure must reconcile approved peers and routes; having a record in the portal alone does not establish a working VPN session.

## Support and negative tests

A person without a completed research profile should be denied key registration; a user must not delete another user's key or alter another programme's approved membership. MFA changes and key revocations should have audited, rate-limited paths; validate duplicate and malformed keys. For a login incident supply timestamps and error/status codes, never cookies or private keys.

Source: [key API](https://github.com/nyameko/quantum-platform/blob/main/apps/user-api/portal/access_keys_api.py), [account security tests](https://github.com/nyameko/quantum-platform/blob/main/apps/user-api/portal/test_account_security.py), [MFA security tutorial](https://github.com/nyameko/quantum-platform/blob/main/docs/tutorials/03-MFA-RESEARCH-WORKFLOWS.md).