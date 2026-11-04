# Account, identity and resource access

## Identity stages

1. Create a personal account using the public sign-up flow and verify the email address.
2. Complete the research profile and institutional information. Enable available MFA under account security before requesting privileged access.
3. Review existing research programmes or make a PI/programme application as appropriate. Programme membership and approval are separate from account registration.
4. An authorized administrator reviews programme/membership requests. **Only approved resource access** may trigger POSIX identity allocation and infrastructure reconciliation.
5. Register SSH and WireGuard **public** keys through the access-key interface, never private keys. Follow the operator-issued provisioning instructions; submitting a key is not proof that a VPN peer or UNIX login is already active.
6. Check the approved allocation/resource offering before submitting a job.

The platform distinguishes human identity, immutable system username (for HPC), programme membership, and AgentPrincipal UUID (for ACP). No one identifier is a substitute for the others. POSIX IDs are allocated from a managed research range and are not recycled. An ACP conversation does not authorize a scheduler allocation.

## Security and recovery

Use the portal's official password reset, verification and MFA recovery processes. Do not place recovery codes or tokens in chat. Ask an administrator for account entitlements, not an agent for an unrestricted shell. Remove stale SSH/WireGuard keys promptly through the authenticated account UI. If a key is compromised, revoke it and rotate it outside a public issue.

## Questions to ask support

Supply username **only through approved support channels**, relevant programme and stage (verification, approval, provisioned, workbench or Slurm) plus a sanitized failure code/time. Never provide password, signing key, SSH private key, WireGuard private key or raw cookies.

Sources: [identity model](https://github.com/nyameko/quantum-platform/blob/main/docs/identity-programmes.md), [access key backend](https://github.com/nyameko/quantum-platform/blob/main/apps/user-api/portal/access_keys_api.py), [identity API](https://github.com/nyameko/quantum-platform/blob/main/apps/user-api/portal/identity_api.py), [MFA tutorial](https://github.com/nyameko/quantum-platform/blob/main/docs/tutorials/03-MFA-RESEARCH-WORKFLOWS.md).