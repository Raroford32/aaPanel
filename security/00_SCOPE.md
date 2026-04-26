# Scope (targeted triage)

Date: 2026-04-25

This was a targeted source-level triage of six externally reported findings against the current repository HEAD:

1. `/static/` unauthenticated traversal
2. `install.sh` remote script execution (`curl | bash`)
3. `business_ssl.check_url_txt` command injection
4. `firewall v2 set_port_rule` command injection
5. `/cloud toserver` CSRF + arbitrary write
6. video filename stored XSS

Method:
- Source validation at current HEAD.
- Route/guard/sink tracing for each claim.
- No destructive runtime exploitation performed.
