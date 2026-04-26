# Residual Risk and Absolute-Vuln Assessment

Date: 2026-04-25

## Can we claim "absolute vulnerability" for all deployments?

No. A universal/absolute claim across every deployment cannot be proven from repository code alone because exploitable reachability depends on deployment controls:
- network exposure and ACLs;
- reverse-proxy normalization behavior;
- runtime secrets and token hygiene;
- additional auth controls (IP allowlists, BasicAuth, etc.);
- operational hardening and patch level.

## What can be claimed with high confidence?

- Prior to hardening, the identified paths were chainable toward critical compromise in common aaPanel deployments.
- After these patches, key chain pivots (path traversal ordering, shell injection vectors, unsafe cloud write composition, stored XSS rendering) were specifically reduced.

## Remaining owner decisions / follow-up

1. Add end-to-end integration tests in a realistic runtime (`/www/server/panel` layout).
2. Add stricter allowlists for cloud download destination roots.
3. Consider removing shell-based curl execution path entirely in favor of non-shell HTTP clients.
4. Consider cryptographic integrity validation for installer helper scripts.
