# Targeted Findings Triage (current HEAD)

## F-01: `/static/` unauthenticated traversal (status: confirmed)

- **Exists at current HEAD:** Yes.
- **Evidence:** In `request_check`, `/static/` uses `request.path` to build filesystem paths and returns `send_file` **before** `path_safe_check`. This happens in an unauthenticated pre-route hook path.  
- **Why it matters:** Can expose sensitive files under panel root if traversal sequences are accepted by request path handling.

## F-02: `install.sh` executes remote script with `curl -k | bash` (status: confirmed)

- **Exists at current HEAD:** Yes.
- **Evidence:** `Install_Python_Lib` runs `curl -sSk ... pip_select.sh | bash`; `-k` disables TLS verification, and script is executed without integrity verification.
- **Why it matters:** Supply-chain/on-path compromise during install/upgrade can yield root code execution.

## F-03: `business_ssl check_url_txt` command injection path (status: confirmed)

- **Exists at current HEAD:** Yes.
- **Evidence:** `check_url_txt` accepts user-controlled `url` and calls `http_requests.get(... s_type='curl')`; `_get_curl` interpolates raw URL into `ExecShell` command.
- **Why it matters:** Authenticated command injection (and SSRF) in panel process context.

## F-04: firewall v2 `port` command injection path (status: confirmed)

- **Exists at current HEAD:** Yes.
- **Evidence:** `set_port_rule` reads `port/s` as string with empty-check only; iptables backend formats shell rule with `info['Port']`; execution via `ExecShell` with shell invocation.
- **Why it matters:** Authenticated command injection in firewall workflow.

## F-05: `/cloud toserver` CSRF claim (status: not reproduced as-stated)

- **Exists at current HEAD:** **Partially**.
- **What changed:** Current `/cloud` and `/v2/cloud` now call `check_csrf()` when `is_csrf=True`, so the “no CSRF check at route level” claim is not accurate for this HEAD.
- **Residual risk still present:** `download_dir` + `name` are still joined into `local_file` without path canonicalization/allowlist, and task execution writes via `wget -O` to that path.
- **Why it matters:** If an attacker has authenticated + valid CSRF context/API-equivalent path, arbitrary-path write remains plausible.

## F-06: Stored XSS via video filename rendering (status: confirmed)

- **Exists at current HEAD:** Yes.
- **Evidence:** Backend returns raw filename in `get_videos`; frontend concatenates filename into HTML strings and injects with `.html(...)` in admin and share playback UIs.
- **Why it matters:** Script execution in panel/share origin when crafted filenames are listed.

---

## Direct answer: “absolute unauth/full takeover?”

- **Absolute guaranteed unauth takeover:** **No** (not guaranteed from source-only review).
- **Plausible unauth → full takeover chain:** **Yes, high-risk and credible** under common deployment assumptions.

### Why “not guaranteed”

- Runtime exposure conditions matter (network reachability, reverse-proxy normalization, secret presence/content, token/session hardening, and extra auth controls).
- Some sinks in this set still require authenticated context.

### Why “plausible critical chain” is still strong

1. Unauthenticated static traversal can disclose sensitive panel config/secrets.
2. Disclosed secrets can enable privileged panel/API context.
3. Authenticated command-injection sinks (`business_ssl` and/or firewall v2) can then execute OS commands.
4. In typical aaPanel privilege models, this can result in full host compromise.

- **Alternative chain:** Stored XSS (attacker-controlled filename) → admin browser execution in panel origin → privileged operations.

## Severity posture at current HEAD

- Overall: **Critical chain risk** when deployment assumptions hold (panel reachable, sensitive files present, attacker can reuse disclosed secrets/tokens).
- Individual bug severities still vary by prerequisites (unauth vs auth vs installer-time).
