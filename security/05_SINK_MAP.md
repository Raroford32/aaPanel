# Sink Map (targeted high-risk flows)

## 1) File send sink (`send_file`) via `/static/`
- **Source:** `request.path`
- **Guard(s):** `public.path_safe_check(request.path)` now before fast-path `send_file`.
- **Sink:** `send_file(static_file)` / `send_file(plugin_static_file)`
- **Status:** Hardened ordering.

## 2) Shell sink via HTTP curl backend
- **Source:** `BusinessSSL.check_url_txt(args.url)`
- **Transform:** `safe_url = shlex.quote(url)`
- **Sink:** `public.ExecShell("curl ... {safe_url}")`
- **Status:** Injection surface reduced for shell metacharacter payloads.

## 3) Shell sink via firewall rule composition
- **Source:** `get.port`
- **Guard(s):** `normalize_port_expression` + range checks
- **Sink:** `public.ExecShell(rule)` in iptables backend
- **Status:** Rejects malformed/non-numeric expressions before sink.

## 4) File write sink via cloud download task
- **Source:** `download_dir`, `get.name`
- **Guard(s):** POST-only, CSRF at route wrapper, `path_safe_check` on both values, basename reduction.
- **Sink:** task engine `wget -O <local_file>`
- **Status:** Arbitrary path attack surface reduced.

## 5) Browser DOM sink in video playback list
- **Source:** `rdata[i].name`, `rdata[i].type`, derived `filename`
- **Guard(s):** `_escapeHtml`, `_escapeJsString`
- **Sink:** dynamic HTML injection + inline onclick argument
- **Status:** Stored-XSS vector mitigated in admin/share lists.
