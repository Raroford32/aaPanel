# AGENTS.md — aaPanel Deep Access-Logic Investigation Protocol

This file is the operating doctrine for AI coding agents, security reviewers, and maintainers investigating this repository for critical access-control and business-logic issues. It is intentionally deeper than a normal checklist. Treat the system as a live, multi-runtime control plane that can mutate the host, not as a simple Flask application.

The goal is not to "find interesting bugs." The goal is to prove, with evidence, whether every sensitive capability is protected by correct identity, session, role, object, origin, method, state, and side-effect controls.

---

## 0. Mission

Investigate aaPanel-style server-management code for critical logic flaws around:

- authentication and session establishment;
- authorization and role enforcement;
- route/action dispatch;
- object-level access control;
- API token and browser-session boundaries;
- CSRF and state-changing browser actions;
- admin-path, APSESS-path, proxy-header, and static-file path normalization;
- plugin, updater, cron, task, shell, Docker, database, file-manager, backup, SSL, DNS, terminal, and firewall workflows;
- local runtime privilege boundaries between panel process, Unix socket, filesystem, plugins, and managed services;
- fail-open behavior caused by exceptions, fallback routes, compatibility layers, or v1/v2 divergence.

A finding is only valid when it includes a reproducible local proof, root cause, affected capability, affected identity class, impact, patch strategy, and regression test.

Do not test against third-party or production systems. All dynamic validation must run in an isolated local VM/container or an explicitly authorized lab.

---

## 1. Mental Model

This repository is a server-control plane, not merely a web UI.

Model the system as:

```text
browser / API client
    -> reverse proxy or direct gevent/WSGI listener
    -> Flask app and before_request hooks
    -> v1/v2 routes and dynamic action dispatch
    -> class / class_v2 controllers
    -> public helpers, DB wrappers, config files, sessions
    -> OS commands, service daemons, sockets, cron, Docker, files, certificates, plugins
```

A route that looks harmless may become critical when its action parameter reaches a controller that can write files, modify config, install software, generate tokens, manage users, execute shell commands, change firewall rules, create cron jobs, read logs, download backups, or proxy data.

The investigation must therefore track:

```text
subject -> request -> route -> action -> guard -> object -> sink -> side effect
```

Never rely on UI visibility, menu hiding, JavaScript checks, path secrecy, or frontend routing as authorization.

---

## 2. Non-Negotiable Agent Rules

1. Work evidence-first. Do not claim a vulnerability from a grep result alone.
2. Prefer source-level reasoning first, then controlled dynamic confirmation.
3. Never perform destructive actions outside an isolated lab.
4. Never run exploit traffic against public demo servers, user installations, or unknown hosts.
5. Do not disclose weaponized exploit chains. Demonstrate issues with minimal local proofs.
6. Do not patch by hiding routes, renaming paths, suppressing errors, or adding frontend-only checks.
7. Every security patch must add or update tests that would fail before the patch.
8. Treat exceptions, broad `try/except`, compatibility fallbacks, and default returns as possible authorization bypass paths.
9. Treat every state-changing GET as suspicious until proven safe.
10. Treat every file path, plugin name, site name, database name, container name, task id, certificate path, backup path, and username as an attacker-controlled object reference until proven otherwise.
11. Treat every generated token as security-critical state with a lifecycle: creation, storage, binding, use, expiry, revocation, logging, and rotation.
12. Treat local-only features as remote-impact features if any route can trigger them.

---

## 3. Required Deliverables

Agents must produce or update these files during a full investigation:

```text
security/00_SCOPE.md
security/01_RUNTIME_MAP.md
security/02_ROUTE_LEDGER.jsonl
security/03_ACCESS_MATRIX.csv
security/04_TRUST_BOUNDARIES.md
security/05_SINK_MAP.md
security/06_FINDINGS.md
security/07_PATCH_PLAN.md
security/08_TEST_PLAN.md
security/09_RESIDUAL_RISK.md
security/evidence/
```

### 3.1 `02_ROUTE_LEDGER.jsonl`

Each line must describe one route/action/capability record:

```json
{
  "route": "/example",
  "methods": ["GET", "POST"],
  "version": "v1|v2|legacy|static|plugin|unknown",
  "handler": "module.function_or_class",
  "dynamic_dispatch": true,
  "action_param": "action",
  "subject_classes": ["unauthenticated", "admin", "subuser", "api_token", "local_process", "plugin"],
  "authn_guard": "function/file/line or none",
  "authz_guard": "function/file/line or none",
  "csrf_guard": "function/file/line or none",
  "object_guard": "function/file/line or none",
  "critical_sinks": ["ExecShell", "writeFile", "send_file", "docker", "database", "cron"],
  "side_effects": ["mutates host", "reads secret", "downloads file"],
  "risk_notes": "short evidence-based note"
}
```

### 3.2 `03_ACCESS_MATRIX.csv`

Columns:

```text
capability, route, method, action, object_type, unauthenticated, pre_login, admin, subuser, api_token, plugin, local_user, csrf_required, ownership_required, audit_logged, expected_result, observed_result, status
```

Use `ALLOW`, `DENY`, `UNKNOWN`, or `NOT_APPLICABLE`. `UNKNOWN` is not acceptable for critical capabilities at the end of the review.

### 3.3 `06_FINDINGS.md`

Each finding must use this structure:

```markdown
## Finding ID

**Title:**
**Severity:** Critical | High | Medium | Low | Informational
**Status:** suspected | confirmed | fixed | false-positive | needs-owner-decision
**Affected capability:**
**Affected routes/actions:**
**Affected identity class:**
**Root cause:**
**Impact:**
**Minimal local proof:**
**Why existing controls failed:**
**Patch design:**
**Regression tests:**
**Residual risk:**
**Evidence:** files, line ranges, logs, screenshots, test output
```

---

## 4. Agent Roles

A single agent may perform multiple roles, but the work must be separated conceptually.

### 4.1 Cartographer Agent

Builds the system map:

- Flask app creation and middleware wrapping;
- `before_request`, `after_request`, `teardown_request`, and error handlers;
- route registration in root app, `BTPanel/routes`, v1, v2, plugins, and dynamic imports;
- compatibility paths, admin path rewrites, APSESS path rewrites, and static-file aliases;
- process entrypoints such as panel startup, task startup, and repair/update scripts;
- privileged helper modules in `class`, `class_v2`, `script`, `install`, `tools.py`, and plugin loaders.

Output: `01_RUNTIME_MAP.md`, initial `02_ROUTE_LEDGER.jsonl`.

### 4.2 Identity and Session Agent

Maps who the system believes the requester is:

- unauthenticated internet client;
- login page visitor;
- authenticated admin;
- restricted subuser;
- API token caller;
- BasicAuth caller;
- APSESS-path caller;
- Google/OAuth callback caller;
- plugin-originated caller;
- local process / Unix-socket caller;
- background task / cron context.

Review session creation, cookie name, cookie flags, server-side session storage, expiry, rotation on login, logout, password change, 2FA change, privilege change, API-key change, and restart.

Output: identity section in `04_TRUST_BOUNDARIES.md` and session rows in `03_ACCESS_MATRIX.csv`.

### 4.3 Authorization Agent

Proves whether every sensitive capability has server-side authorization.

Do not count these as sufficient authorization by themselves:

- menu filtering;
- frontend route hiding;
- admin path secrecy;
- static path filtering;
- request length filtering;
- method filtering;
- IP allowlisting alone;
- domain binding alone;
- BasicAuth alone when session auth is required;
- broad `login in session` checks for role-sensitive operations.

Output: completed `03_ACCESS_MATRIX.csv`, authorization findings.

### 4.4 Object Ownership Agent

Tracks object identifiers from request to data access:

- site name / site id;
- FTP account;
- database name/user;
- file path;
- backup name/path;
- certificate id/path/domain;
- DNS provider account;
- Docker container/image/volume/network;
- cron id;
- plugin name/version;
- user id;
- firewall rule id;
- log path;
- project id.

For every object type, prove whether a subuser or API caller can read or mutate objects outside its permitted scope.

Output: object sections in `03_ACCESS_MATRIX.csv` and `05_SINK_MAP.md`.

### 4.5 Sink and Side-Effect Agent

Builds the sink map:

- command execution: `ExecShell`, `os.system`, `subprocess`, shell wrappers, cron, service reloads;
- file read/write/delete/copy/move/chmod/chown, especially across `/www/server/panel`, `/www/wwwroot`, `/tmp`, SSL directories, backup directories, and config/data files;
- download/stream/send-file responses;
- SQL operations and DB-user management;
- Docker API operations;
- network fetches, update checks, plugin downloads, webhook callbacks;
- SSH/terminal/PTY paths;
- certificate/private-key operations;
- token, password, OTP, API-key creation or reset;
- firewall and system-service mutation.

Output: `05_SINK_MAP.md`, sink-linked route ledger rows.

### 4.6 Patch Agent

Only patches after the above agents provide evidence.

Patch rules:

- centralize authorization when possible;
- do not depend on frontend state;
- prefer deny-by-default;
- bind authorization to concrete capability and object;
- preserve intended admin workflows;
- log denied critical attempts without leaking secrets;
- include regression tests.

Output: patch, tests, and `07_PATCH_PLAN.md`.

### 4.7 Regression Agent

Creates tests for:

- unauthenticated denial;
- subuser denial;
- admin allow;
- API token allow/deny according to policy;
- CSRF-required browser mutation denial;
- object ownership denial;
- path traversal denial;
- action-dispatch denial for unknown or restricted actions;
- v1/v2 parity;
- plugin route parity;
- fail-closed behavior on malformed input and internal guard exceptions.

Output: `08_TEST_PLAN.md`, automated test files.

---

## 5. Repository Surfaces to Prioritize

The first-pass focus areas are:

```text
BTPanel/__init__.py            Flask app, middleware, hooks, session, route imports
BTPanel/app.py                 app-level compatibility or legacy behavior
BTPanel/routes/                v1/v2/flask hook route definitions
class/                         legacy controllers and privileged helpers
class_v2/                      v2 controllers and privileged helpers
config/                        default policy, menus, APIs, weak password lists, script types
data/                          runtime security state when present in deployment
install/ and script/           install, update, repair, task, and service flows
tools.py                       admin repair, auth reset, BasicAuth/2FA operations
BT-Panel and BT-Task           process startup, task daemon, gevent, Unix socket, background jobs
plugin/ if present at runtime  plugin route/action/loader trust boundary
```

High-risk controller domains include:

```text
files, panelSite, panelPlugin, panelSafe, panelSSL, panelApi, panelAuth,
panelController, panelDatabaseController, panelProjectController, crontab,
database, ftp, firewalls, firewall_new, docker/btdocker, webssh/xterm,
backup, download, config, logs, monitor, public helpers, update/repair flows
```

Do not skip duplicated or legacy-looking files. v1/v2 divergence is a prime source of access logic errors.

---

## 6. Critical Capability Catalogue

Every capability below must have explicit server-side authn, authz, object checks, method checks, CSRF posture, audit posture, and safe failure behavior.

### 6.1 Identity and Credential Capabilities

- login;
- logout;
- password change;
- password reset/repair;
- username change;
- API key generation, enablement, disablement, rotation;
- BasicAuth enablement, disablement, and credential change;
- 2FA/OTP enablement, disablement, recovery, reset;
- session token creation and revocation;
- APSESS URL token creation and validation;
- OAuth/Google callback handling;
- admin-path creation/change;
- IP allowlist and domain binding changes;
- subuser creation, deletion, role change, menu assignment.

### 6.2 Host-Mutation Capabilities

- run shell command;
- install/update/remove plugin;
- repair/update panel;
- create/edit/delete file;
- archive/extract/upload/download file;
- chmod/chown/copy/move path;
- create cron job;
- modify service config;
- start/stop/restart/reload service;
- change firewall rule;
- add/remove site;
- modify virtual host;
- create/edit/delete database or DB user;
- backup/restore site or database;
- create/delete Docker container/image/volume/network;
- terminal/webssh/xterm operation;
- install runtime packages or webserver components.

### 6.3 Secret-Handling Capabilities

- read private key;
- download certificate;
- view DNS API credential;
- view database password;
- view FTP password;
- view backup archive;
- read panel config files;
- read logs containing tokens or secrets;
- export user/session/API-token state;
- plugin-store credentials or cloud-storage credentials.

### 6.4 External Trust Capabilities

- download plugin/update metadata;
- call cloud APIs;
- DNS provider API calls;
- webhook-triggered deployment;
- Git clone/pull and auto-update;
- Docker registry pull;
- third-party storage upload/download;
- email or notification integrations.

---

## 7. Access-Logic Invariants

These invariants are mandatory. When an invariant does not hold, open a finding or document why the capability is intentionally exempt.

### 7.1 Authentication Invariants

1. No privileged route is reachable without a valid authenticated identity.
2. Login creates a fresh server-side session and does not reuse attacker-supplied privilege state.
3. Logout clears all privilege-bearing session keys.
4. Password change, password expiry, 2FA changes, API-key rotation, and user deletion invalidate or downgrade affected sessions.
5. Debug mode cannot bypass authentication in production-like configurations.
6. API-token authentication and browser-session authentication are not interchangeable unless explicitly intended.
7. BasicAuth cannot promote an unauthenticated request into a panel-admin action unless the route explicitly allows that model.
8. APSESS URL tokens are bound to the correct session/user and cannot be replayed, doubled, normalized around, or used as a substitute for login.

### 7.2 Authorization Invariants

1. Every privileged route checks authorization server-side.
2. Every privileged action in dynamic dispatch checks authorization, not only the route wrapper.
3. Every object operation checks that the subject may access the specific object.
4. Restricted users cannot reach hidden menu operations by direct URL, API call, alternate route, v1 route, v2 route, plugin route, or action parameter.
5. Authorization failures return denial before side effects.
6. Guard exceptions fail closed.
7. Admin-only actions are encoded as admin-only in code, not inferred from UI layout.
8. Batch operations authorize each object, not only the batch request.
9. Time-delayed operations, queued jobs, and cron-created operations preserve the initiating subject and authorization decision.

### 7.3 CSRF and Browser-Origin Invariants

1. Browser-session state-changing requests require CSRF protection or an equivalent same-origin proof.
2. GET requests do not mutate state. Any exception must be justified and protected.
3. CSRF checks apply equally to v1, v2, plugin, legacy, and admin-path-prefixed routes.
4. CSRF tokens are bound to session and expire.
5. JSON endpoints are not exempt merely because they are XHR-style endpoints.
6. CORS, if present, does not permit credentialed cross-origin mutation.

### 7.4 Path and Static-File Invariants

1. Path normalization occurs before authorization-sensitive comparisons.
2. Decoded, encoded, doubled-slash, dot-segment, symlink, Unicode, and APSESS-prefixed paths resolve consistently.
3. Static-file handling cannot read plugin or panel files outside intended static directories.
4. `send_file`, archive extraction, backup download, certificate download, and log download use canonical allowlisted paths.
5. File writes cannot replace security-critical panel files unless the caller has explicit admin-level file-management authority and the path is intended to be mutable.
6. Temporary files and Unix sockets are permissioned to the narrowest needed users.

### 7.5 Runtime and Side-Effect Invariants

1. The panel process does not expose unauthenticated local sockets or world-writable control channels that can mutate host state.
2. Background tasks do not run attacker-controlled commands from untrusted request state.
3. Plugin installation/update verifies trust before code execution.
4. Update/repair flows do not allow untrusted paths, URLs, or command fragments.
5. Service reload/restart flows cannot be triggered by unauthorized subjects.
6. Failure in a precondition does not continue into side-effect code.

---

## 8. Investigation Workflow

### Phase A — Build the Runtime Map

1. Identify entrypoints:
   - panel web process;
   - task process;
   - install/update scripts;
   - admin repair tools;
   - plugin loader;
   - cron/background jobs.
2. Identify Flask app initialization and global hooks.
3. Identify all route imports and dynamic route registration.
4. Identify all request-time gates:
   - auth checks;
   - IP/domain checks;
   - BasicAuth checks;
   - APSESS token checks;
   - CSRF checks;
   - path filters;
   - method filters;
   - menu/subuser checks.
5. Draw the request pipeline in `01_RUNTIME_MAP.md`.

### Phase B — Build the Route and Action Ledger

Enumerate:

- `@app.route`, blueprints, decorators, sockets;
- dynamic dispatch via `action`, `mod`, `name`, `type`, `project_type`, `plugin`, or similar parameters;
- route aliases caused by admin path prefixes;
- static handlers;
- download handlers;
- plugin handlers;
- v1 and v2 duplicate functionality.

For each route, identify:

```text
route -> method -> handler -> action -> controller -> guard -> object -> sink
```

### Phase C — Build the Subject/Object/Capability Matrix

For each critical capability, test or reason for:

```text
unauthenticated
pre-login session
admin session
restricted subuser session
API-token caller
BasicAuth-only caller
plugin context
local process context
```

The expected default is `DENY` unless a capability is explicitly public.

### Phase D — Challenge the Guards

For each guard, ask:

- Does it run before any side effect?
- Does it cover every route alias?
- Does it cover every method?
- Does it cover every action in dynamic dispatch?
- Does it cover v1 and v2?
- Does it cover plugin routes?
- Does it cover queued/background effects?
- Does it bind to object ownership?
- What happens if the guard throws an exception?
- What happens if session keys are missing, malformed, stale, or partially present?
- What happens if request headers spoof proxy IPs?
- What happens if path normalization changes after the guard?

### Phase E — Trace Data to Critical Sinks

For each source:

```text
request.args
request.form
request.json
request.files
cookies
headers
session
config files
database rows
plugin metadata
external update metadata
cron/task state
```

Trace to sinks:

```text
ExecShell/os.system/subprocess
public.writeFile/public.readFile
open/shutil/zip/tar/rar operations
send_file/Response streaming
SQL execution/ORM wrappers
Docker client calls
paramiko/SSH/PTY/web terminal
cron/task scheduling
service restart/reload
certificate/private-key writes
plugin loader/imports
network requests/downloads
```

Document every unguarded or weakly guarded path in `05_SINK_MAP.md`.

### Phase F — Controlled Dynamic Confirmation

Use only an isolated lab. Confirm only enough to prove the logic flaw.

For each suspected issue:

1. Start from least privilege.
2. Use a minimal benign object, such as a test site, test file, test database, or test cron comment.
3. Demonstrate allow/deny mismatch without destructive impact.
4. Capture request, response, server log, and before/after state.
5. Add regression test.

### Phase G — Patch and Prove

A patch is incomplete until:

- tests fail before the patch;
- tests pass after the patch;
- no adjacent route alias remains open;
- the access matrix is updated;
- residual risk is documented.

---

## 9. Static Discovery Commands

Run these locally from the repo root. Redirect outputs to `security/evidence/`.

### 9.1 Route Discovery

```bash
mkdir -p security/evidence
rg -n --hidden --glob '!*.min.js' \
  "(@app\.route|add_url_rule|Blueprint\(|Sock\(|@sockets\.route|route\(|request\.path|request\.endpoint)" \
  BTPanel class class_v2 > security/evidence/routes.rg.txt || true
```

### 9.2 Dynamic Dispatch Discovery

```bash
rg -n --hidden \
  "(request\.(args|form|json|get_json)|getattr\(|hasattr\(|__import__\(|importlib|action|mod|plugin|project_type|type\s*=|name\s*=)" \
  BTPanel class class_v2 > security/evidence/dynamic-dispatch.rg.txt || true
```

### 9.3 Authentication and Authorization Discovery

```bash
rg -n --hidden \
  "(session\[|session\.get|login|uid|username|password|token|csrf|auth|BasicAuth|BASIC_AUTH|check_ip|check_domain|admin_path|user_router_authority|permission|role|menu|api|APSESS|apsess)" \
  BTPanel class class_v2 config tools.py BT-Panel BT-Task > security/evidence/authz.rg.txt || true
```

### 9.4 Critical Sink Discovery

```bash
rg -n --hidden \
  "(ExecShell|os\.system|subprocess|Popen|run\(|call\(|eval\(|exec\(|open\(|writeFile|readFile|send_file|send_from_directory|Response\(|chmod|chown|remove\(|unlink\(|rmtree|copyfile|move\(|zipfile|tarfile|rarfile|docker|paramiko|crontab|iptables|firewall|systemctl|service\s|nginx|apache|mysql|redis|privateKey|certificate|pem|keyfile|certfile)" \
  BTPanel class class_v2 script install tools.py BT-Panel BT-Task > security/evidence/sinks.rg.txt || true
```

### 9.5 Error and Fail-Open Discovery

```bash
rg -n --hidden \
  "(except\s*:|except Exception|return\s+True|return\s+False|abort\(|redirect\(|pass$|continue$|try:)" \
  BTPanel class class_v2 > security/evidence/fail-open.rg.txt || true
```

### 9.6 Secrets and Credential Handling Discovery

```bash
rg -n --hidden \
  "(secret|private|password|passwd|pwd|token|api_key|apikey|access_key|secret_key|otp|totp|cookie|session|credential|authorization|basic_user|basic_pwd)" \
  BTPanel class class_v2 config script install tools.py > security/evidence/secrets.rg.txt || true
```

---

## 10. AST-Level Route and Guard Inventory

Prefer AST extraction over grep when possible. Create `security/tools/route_inventory.py` if it does not exist:

```python
#!/usr/bin/env python3
import ast
import json
import pathlib
import sys

ROOTS = ["BTPanel", "class", "class_v2"]


def dotted(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = dotted(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    if isinstance(node, ast.Call):
        return dotted(node.func)
    return ""


def literal(node):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return [literal(x) for x in node.elts]
    return None


def decorators(fn):
    out = []
    for dec in getattr(fn, "decorator_list", []):
        if isinstance(dec, ast.Call):
            out.append({
                "decorator": dotted(dec.func),
                "args": [literal(a) for a in dec.args],
                "kwargs": {kw.arg: literal(kw.value) for kw in dec.keywords if kw.arg},
            })
        else:
            out.append({"decorator": dotted(dec), "args": [], "kwargs": {}})
    return out


def calls(tree):
    names = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            name = dotted(n.func)
            if name:
                names.append(name)
    return sorted(set(names))


def main():
    for root in ROOTS:
        for path in pathlib.Path(root).rglob("*.py"):
            try:
                text = path.read_text(errors="ignore")
                tree = ast.parse(text)
            except Exception as e:
                print(json.dumps({"path": str(path), "parse_error": str(e)}))
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    decs = decorators(node)
                    route_decs = [d for d in decs if "route" in d["decorator"].lower() or "websocket" in d["decorator"].lower()]
                    if route_decs:
                        print(json.dumps({
                            "path": str(path),
                            "line": node.lineno,
                            "function": node.name,
                            "decorators": route_decs,
                            "calls": calls(node),
                        }, ensure_ascii=False))

if __name__ == "__main__":
    sys.exit(main())
```

Run:

```bash
mkdir -p security/tools security/evidence
python3 security/tools/route_inventory.py > security/evidence/route_inventory.jsonl
```

Manual follow-up is required for dynamic routes, action dispatch, plugins, and controllers reached indirectly.

---

## 11. Access-Logic Attack Classes to Investigate Defensively

Use this taxonomy to organize review. Do not write weaponized exploit instructions; produce controlled proofs only.

### 11.1 Missing Authentication

Pattern:

```text
route/action reaches critical sink without requiring a valid session/API identity
```

Common causes:

- allowlist path grows over time;
- route imported outside main guard assumptions;
- plugin route bypasses central hooks;
- error handler returns useful data before auth;
- static/download route treats attacker path as static asset;
- BasicAuth or APSESS check substitutes for session incorrectly.

### 11.2 Broken Function-Level Authorization

Pattern:

```text
restricted user can call an admin-only function directly
```

Common causes:

- UI menu filtering but no handler-level permission;
- dynamic `action` dispatch not permissioned per action;
- v1 route allows what v2 denies;
- plugin API route lacks same guard as built-in route;
- batch operation checks only outer route.

### 11.3 Broken Object-Level Authorization

Pattern:

```text
user has some access to a resource type but can access another user/scope's object
```

Common causes:

- site id not checked against user's assigned sites;
- file path not constrained to permitted root;
- database/user name accepted directly;
- backup/cert/log path accepted directly;
- Docker resource id accepted directly;
- cron id accepted directly.

### 11.4 CSRF on Host-Mutation

Pattern:

```text
browser-authenticated request mutates host state without same-origin proof
```

Common causes:

- JSON endpoints exempted;
- GET mutates state;
- action dispatch bypasses CSRF wrapper;
- plugin endpoints omitted;
- token checked only on frontend;
- token not bound to session.

### 11.5 Path Canonicalization Bypass

Pattern:

```text
a guard checks one representation of a path, but the sink uses another
```

Common causes:

- URL decode order mismatch;
- APSESS/admin-path prefix stripping;
- repeated slashes;
- dot segments;
- symlinks;
- Unicode normalization;
- archive extraction paths;
- static-file fallback paths;
- plugin static paths.

### 11.6 State Confusion

Pattern:

```text
security decision depends on mutable or partially initialized state
```

Common causes:

- session key presence instead of verified identity;
- stale password-expiry or role state cached in session;
- config flags stored in writable files;
- process restart changes secrets and leaves old state ambiguous;
- background task executes old authorization decision after user role changed;
- failed login or setup flow leaves privileged session keys.

### 11.7 Alternate-Channel Bypass

Pattern:

```text
one channel has correct checks; another equivalent channel does not
```

Channels:

- browser page route;
- XHR endpoint;
- v1 endpoint;
- v2 endpoint;
- plugin endpoint;
- API-token endpoint;
- BasicAuth endpoint;
- WebSocket endpoint;
- Unix socket / local proxy path;
- background task;
- repair/update tool.

### 11.8 Guard Fail-Open

Pattern:

```text
exception, missing dependency, missing config, malformed session, or unexpected method causes allow instead of deny
```

Evidence should include the exact guard branch and why denial was skipped.

### 11.9 Confused Deputy

Pattern:

```text
low-privileged subject causes high-privileged panel process to perform an action on its behalf
```

High-risk deputies:

- file manager;
- plugin installer;
- backup/restore;
- cron scheduler;
- terminal;
- Docker manager;
- SSL/DNS automation;
- update/repair scripts;
- Git/webhook deployment.

---

## 12. Specialized Deep Dives

### 12.1 `before_request` Deep Dive

For each global hook:

1. List every early `return`.
2. Classify it as deny, allow, redirect, static send, or no-op.
3. Determine whether later security checks are skipped.
4. List path exceptions and why they exist.
5. Check whether exceptions are exact-match, prefix-match, substring-match, or regex-match.
6. Check whether normalized path and raw path differ.
7. Check whether query/action affects the guard.
8. Check whether v2/plugin/static/admin-path/APSESS paths flow through the same checks.

Output table:

```text
branch | condition | skipped_checks | side_effect_possible | expected | observed | risk
```

### 12.2 APSESS URL Token Deep Dive

Investigate:

- generation entropy;
- binding to session/user/IP/user-agent if intended;
- normalization of repeated `apsess_` prefixes;
- stripping before path checks;
- interaction with admin path;
- replay after logout/password change;
- leakage through logs, Referer, redirects, static asset URLs;
- behavior on malformed token;
- behavior when token exists but session is unauthenticated.

Expected result: APSESS path mechanics must never act as authentication alone.

### 12.3 Admin Path Deep Dive

Investigate:

- how admin path is stored;
- reserved path collisions;
- fallback to `/bt`;
- prefix matching vs exact matching;
- static asset behavior under admin path;
- redirects leaking admin path;
- interaction with APSESS and plugin static routes;
- whether changing admin path invalidates old URLs/sessions where intended.

Expected result: admin-path secrecy may reduce noise but must not be required for authorization.

### 12.4 Subuser/Menu Authorization Deep Dive

Investigate:

- whether menu visibility equals permission or only UI preference;
- whether direct endpoint calls are denied;
- whether action-level restrictions exist;
- whether object-level restrictions exist;
- whether v1/v2 duplicate actions agree;
- whether restricted user can use batch APIs;
- whether restricted user can use plugin APIs;
- whether restricted user can create cron/plugin/file changes that execute as admin/root later.

Expected result: route/action/object permissions must be enforced server-side independently of menus.

### 12.5 API Token Deep Dive

Investigate:

- token generation and storage;
- token display and redaction;
- token revocation;
- IP/domain restrictions;
- permission scope;
- whether API token bypasses CSRF appropriately without gaining browser-only privileges;
- whether API token can access endpoints that expect session state;
- whether API token requests clear or mutate browser session state;
- whether API token logs leak secrets.

Expected result: API token is an independent identity class with explicit capabilities.

### 12.6 Plugin Deep Dive

Investigate:

- plugin installation source validation;
- signature/hash verification if any;
- plugin route registration;
- plugin static-file serving;
- plugin update/uninstall permissions;
- plugin file write locations;
- plugin loader native modules;
- plugin access to `public` helpers and session;
- whether plugin actions bypass v1/v2 core authorization;
- whether plugin metadata controls imports, paths, or commands.

Expected result: no plugin-originated action executes privileged host mutations without explicit trust and authorization.

### 12.7 File Manager Deep Dive

Investigate:

- canonical root restrictions;
- symlink behavior;
- archive extraction behavior;
- upload extension checks;
- chmod/chown effects;
- editing panel files or plugin files;
- backup download path;
- log read path;
- certificate/private-key read path;
- webroot-to-panel traversal;
- permission model for subusers.

Expected result: every path sink resolves to an allowed canonical root before use.

### 12.8 Cron and Task Deep Dive

Investigate:

- who can create tasks;
- what commands/scripts can be scheduled;
- whether task executes as root/panel user;
- whether delayed execution preserves initiator identity;
- whether disabled/deleted users' tasks continue;
- whether task logs expose secrets;
- whether task modification endpoints enforce object ownership.

Expected result: a low-privilege user cannot schedule high-privilege host actions.

### 12.9 Docker Deep Dive

Investigate:

- container create/exec permissions;
- volume mounts;
- privileged mode;
- host network;
- image pull sources;
- registry credentials;
- object ownership for containers/projects;
- whether Docker actions can reach panel filesystem or host socket.

Expected result: Docker control is treated as host-level critical unless carefully sandboxed.

### 12.10 SSL/DNS Deep Dive

Investigate:

- DNS API credential storage and display;
- certificate private-key download;
- domain ownership checks;
- ACME challenge file paths;
- wildcard certificate flows;
- renewal cron jobs;
- certificate deployment to vhost;
- permissions for subusers.

Expected result: secret exposure and domain/cert mutation require explicit authorization.

### 12.11 Backup/Restore Deep Dive

Investigate:

- backup path creation;
- backup archive download;
- restore path validation;
- archive extraction path traversal;
- database restore target selection;
- cloud storage credentials;
- object ownership for backup files;
- backup logs containing secrets.

Expected result: restore/download cannot cross object boundaries or overwrite security-critical files.

### 12.12 Update/Repair Deep Dive

Investigate:

- update source validation;
- script paths;
- command construction;
- offline mode restrictions;
- who can trigger update/repair;
- whether local files can influence update scripts;
- whether restart/reload behavior can be abused;
- whether updater modifies auth/security files.

Expected result: update/repair is admin-only, integrity-checked, and not influenced by untrusted request fields.

---

## 13. Runtime Investigation Guidance

Static analysis is insufficient for a multi-process control plane. In a lab, capture runtime state.

### 13.1 Process and Socket Map

```bash
ps auxww | tee security/evidence/ps.txt
ss -ltnupx | tee security/evidence/sockets.txt
lsof -nP -p <PANEL_PID> | tee security/evidence/lsof-panel.txt
find /tmp -maxdepth 2 -type s -o -type p -o -type f | tee security/evidence/tmp-objects.txt
```

Review:

- listener address and port;
- Unix socket path and permissions;
- process user;
- environment variables;
- open config/session/log files;
- child processes and task daemons.

### 13.2 Request Decision Tracing

For local-only debugging, instrument guard decisions rather than guessing. Log:

```text
request id
raw path
normalized path
method
session keys present, not values
identity class
authentication decision
authorization decision
csrf decision
object decision
selected handler/action
critical sink reached or not
```

Never log passwords, cookies, private keys, API tokens, OTP seeds, or full authorization headers.

### 13.3 Minimal Dynamic Access Tests

For each tested endpoint, perform the same request as:

```text
no cookie
invalid cookie
authenticated admin
restricted user with no permission
restricted user with adjacent permission
API token when applicable
browser session without CSRF when applicable
```

Capture only safe, non-destructive state transitions.

---

## 14. Patch Design Patterns

### 14.1 Central Capability Gate

Preferred shape:

```python
def require_capability(capability: str, obj=None):
    identity = current_identity()
    if not identity.is_authenticated:
        raise AuthnDenied()
    if not policy.allows(identity, capability, obj):
        raise AuthzDenied()
    return identity
```

Every sensitive action should call a capability-specific gate before side effects.

### 14.2 Dynamic Dispatch Gate

Bad pattern:

```python
if session.get("login"):
    return getattr(controller, request.form["action"])(request)
```

Required pattern:

```python
action = parse_action(request)
capability = ACTION_CAPABILITY_MAP.get(action)
if capability is None:
    deny_unknown_action()
obj = resolve_object_for_action(action, request)
require_capability(capability, obj)
return dispatch(action, request)
```

Unknown actions must deny. Capability maps must be reviewed in tests.

### 14.3 Object Authorization Pattern

Required order:

```text
parse object reference
canonicalize/resolve object
load object from trusted store
verify subject may access object
only then perform side effect
```

Do not authorize raw request strings.

### 14.4 CSRF Pattern

For browser-session mutations:

```text
require authenticated session
require unsafe method only for mutation: POST/PUT/PATCH/DELETE
require CSRF token bound to session
perform capability and object check
perform side effect
```

Do not make state-changing GET exceptions unless documented and equivalently protected.

### 14.5 Path Safety Pattern

Required order:

```text
raw input
URL decode once under framework rules
normalize Unicode if relevant
join with intended root
resolve symlinks with realpath
verify resolved path is inside allowed root
open using safe mode
avoid TOCTOU where possible
```

For archive extraction, validate every member path before extraction.

### 14.6 Fail-Closed Pattern

Any failure in security context creation must deny:

```python
try:
    identity = current_identity()
    allowed = policy.allows(identity, capability, obj)
except Exception:
    security_log("guard_error", capability=capability)
    return deny()
```

---

## 15. Test Strategy

### 15.1 Test Classes

Create tests around security behavior, not just successful workflows.

Required classes:

```text
TestUnauthenticatedDenial
TestSubuserFunctionAuthorization
TestObjectOwnership
TestCsrfRequiredForMutation
TestV1V2AuthorizationParity
TestDynamicActionDispatch
TestPathCanonicalization
TestPluginRouteAuthorization
TestApiTokenBoundary
TestFailClosedGuards
```

### 15.2 Test Matrix Template

For each critical endpoint/action:

```text
identity x method x csrf x object x route_alias x version
```

At minimum:

```text
unauthenticated + valid params -> deny
admin + valid params -> allow
subuser without permission + valid params -> deny
subuser with adjacent permission + different object -> deny
admin + missing csrf on browser mutation -> deny
malformed object id -> deny before sink
unknown action -> deny before sink
v1/v2 equivalent action -> same authz result
```

### 15.3 Sink-Blocking Tests

When testing denial, assert both response and absence of side effect:

- file not created/modified;
- command not invoked;
- DB row not changed;
- cron not created;
- Docker action not called;
- certificate not downloaded;
- plugin not installed;
- service not restarted.

Use mocks/spies for dangerous sinks.

---

## 16. Severity Model

Severity depends on capability, identity class, and exploitability in the authorized lab model.

### Critical

- unauthenticated or low-privileged path to host command execution;
- unauthenticated or low-privileged admin takeover;
- unauthorized API-key/session/token creation;
- unauthorized plugin install/update leading to code execution;
- unauthorized file write to panel, cron, service config, authorized keys, or executable path;
- unauthorized Docker host-level control;
- private-key or credential exfiltration with broad impact;
- CSRF that can trigger host-level destructive or code-execution actions from an admin browser.

### High

- subuser can perform admin-only host mutations;
- object-level bypass for sensitive files, databases, backups, certificates, or sites;
- state-changing GET or missing CSRF for high-impact mutation;
- API token bypasses intended scope;
- v1/v2 alternate route bypasses authz;
- update/repair flow can be triggered without proper authorization.

### Medium

- restricted data exposure without direct host compromise;
- weak session lifecycle issue requiring prior auth;
- inconsistent denial behavior that leaks metadata;
- missing audit log for sensitive action;
- guard fail-open in uncommon configuration.

### Low / Informational

- hardening gaps without demonstrated access violation;
- ambiguous policy requiring maintainer decision;
- missing tests for security behavior;
- confusing but non-bypassable routing.

---

## 17. Evidence Standards

Every claim must cite at least one of:

- file and line range;
- route ledger row;
- access matrix row;
- test name and output;
- captured local request/response;
- local server log;
- before/after filesystem or DB state;
- patch diff.

Use cautious language:

- "confirmed" only after local proof;
- "suspected" when source path suggests risk but no proof exists;
- "not reproduced" when a path was tested and denied;
- "policy decision" when code behavior is clear but desired behavior requires owner input.

---

## 18. Review Questions for Every High-Risk Function

Ask these questions before closing a file:

1. Who can call this function directly?
2. Who can reach it through dynamic dispatch?
3. Which route aliases reach it?
4. Which v1/v2/plugin variants exist?
5. What objects does it read or mutate?
6. Are those objects authorized per subject?
7. Does it trust request strings as paths, ids, names, or commands?
8. Does it reach a critical sink?
9. Does it mutate state on GET?
10. Does it require CSRF for browser-session mutation?
11. Does it behave differently under BasicAuth, API token, APSESS, admin path, or proxy headers?
12. Does it queue delayed work?
13. Does delayed work preserve authorization context?
14. What happens if validation or guard code throws?
15. Is denial logged without leaking secrets?
16. Is there a regression test?

---

## 19. Common False Positives to Avoid

Do not report as a vulnerability without proof:

- a dangerous sink that is unreachable by untrusted subjects;
- a static file path that is fully canonicalized and allowlisted;
- an admin-only feature that is dangerous by design but correctly restricted;
- a menu-hidden action that is also correctly denied server-side;
- an API endpoint that is intentionally public and has no sensitive side effect;
- a test-only or install-only script that cannot run after deployment without admin/local access.

Still document hardening recommendations separately when appropriate.

---

## 20. Red Flags That Deserve Immediate Attention

Open a suspected finding quickly when any of these appear near critical sinks:

- `session.get("login")` with no role/capability/object check;
- `uid` check only for page render but not action endpoint;
- `action = request...` followed by `getattr` or dynamic import;
- allowlisted public path reaching controller methods;
- state mutation in a GET handler;
- route-level auth but unguarded background task executing later;
- `try/except: pass` around auth, path, or token checks;
- `return` before auth checks in global hook;
- path check before prefix stripping or after partial decoding;
- `send_file` on request-controlled path;
- shell command built from request-controlled fields;
- plugin metadata controlling import path, command, or file write;
- v1 endpoint missing checks present in v2;
- subuser menu policy used as authorization;
- client-side JavaScript enforcing a server-side policy;
- API token request using browser session side effects;
- BasicAuth exceptions for sensitive paths;
- world-writable socket or temporary control file;
- config/data file controls security state and is writable by a lower-privileged path.

---

## 21. Definition of Done

The investigation is complete only when:

1. Every route/action with a critical sink is represented in `02_ROUTE_LEDGER.jsonl`.
2. Every critical capability has a completed row in `03_ACCESS_MATRIX.csv`.
3. v1/v2/plugin/admin-path/APSESS alternate channels are checked for parity.
4. All `UNKNOWN` entries for critical capabilities are resolved.
5. Confirmed findings include local proof and tests.
6. Patches are minimal, server-side, deny-by-default, and regression-tested.
7. Residual risks are documented with owner decisions.
8. No finding relies only on UI behavior or scanner output.

---

## 22. First 48-Hour Execution Plan for Agents

### Pass 1 — Map

- Generate grep evidence files.
- Generate AST route inventory.
- Build runtime map.
- Identify top 30 critical sinks.
- Identify all public/allowlisted path exceptions.

### Pass 2 — Model

- Build first route ledger.
- Build first access matrix.
- Mark all dynamic dispatch points.
- Mark all v1/v2 duplicated capabilities.
- Mark all object identifiers.

### Pass 3 — Challenge

- Test unauthenticated denial for critical routes.
- Test restricted-user denial for admin-only actions.
- Test CSRF denial for browser mutations.
- Test object-boundary denial for file/site/database/backup/cert/cron/plugin objects.
- Test v1/v2 parity for equivalent actions.

### Pass 4 — Patch

- Patch confirmed issues only.
- Add tests first when feasible.
- Update evidence and matrix.
- Document residual risk.

---

## 23. Output Tone and Communication

Security reports must be precise and calm.

Use:

```text
"The route appears to allow..."
"The guard is present but does not bind to..."
"This was confirmed locally with..."
"The impact is limited to..."
"I did not reproduce..."
```

Avoid:

```text
"This is definitely RCE" without proof
"Looks vulnerable" without route/action/sink evidence
"Scanner says" without source validation
"Impossible to exploit" without testing alternate channels
```

---

## 24. Final Reminder

This system manages servers. Access-control mistakes can become host compromise even when the vulnerable route looks like ordinary panel administration. Think in capabilities, not pages. Think in object boundaries, not forms. Think in side effects, not responses. Think in alternate channels, not the happy path.

The best finding is not the cleverest trick. The best finding is the one that proves a broken security invariant and leaves behind a test that prevents it forever.
