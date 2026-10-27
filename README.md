# MEARCO Assist 24/7 — standalone upgrade v0.2

Standalone starter upgraded with a customer-facing `/assist` page, private `/track` case status, protected MEARCO dashboard `/`, Excel upload `/policies`, and a separate provider job board `/provider`. Telephone, SMS, WhatsApp, live vehicle tracking and AI are **not** integrated. No automated alert or dispatch is performed.

## Deploy
Replace the repository files with all contents of this folder, preserving `templates/` and `static/`. Same Render Web Service, same start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`; build: `pip install -r requirements.txt`.

Required Render environment variables:
- `ADMIN_PASSWORD` unique strong credential
- `SESSION_SECRET` random 32+ character secret

Optional:
- `PROVIDER_PASSWORD` separate strong password (required for provider login)
- `PUBLIC_INTAKE_ENABLED=0` (default; set to `1` **only after** staffed monitoring, privacy/security approval and durable database setup)
- `PUBLIC_TRACKING_ENABLED=0` (default; set to `1` only when public intake is approved)
- `DB_PATH=/var/data/assist.sqlite3` **only when Render persistent disk is mounted at `/var/data`**. Otherwise this demo stores SQLite in ephemeral app filesystem and data may vanish on deploy/restart.

## Safety and release restrictions
This is an **internal TEST prototype**. It uses a single administrator password, a shared provider password and SQLite; this is NOT production-ready identity management. Public intake is disabled by default. Do not use real customers, policyholder data, claims, or telephone numbers. Do not advertise this as an active 24/7 service. No real call/WhatsApp/notification, on-call coverage guarantee, automatic ETA, or automatic towing dispatch exists. The on-prem or Render database should be secured with backups and tested restore, individual staff identities/MFA, role-scoped provider accounts, privacy notice/consent/retention, centralized abuse protection/WAF and scheduled security review before enabling production.

## Demo testing
1. Login `/login` with `ADMIN_PASSWORD`. Add fake case at `/`.
2. Assign a sample towing provider via case details.
3. Set `PROVIDER_PASSWORD`, open `/provider/login`, update dispatch and inspect audit trail.
4. Add fake policy via `/policies` or import template `static/policy_template.csv`.
5. Visit `/assist`. It deliberately displays a not-yet-active notice until production prerequisites have been satisfied.

IMPORTANT: If you change from ephemeral SQLite to persistent PostgreSQL later, implement a tested migration instead of assuming the old records will move automatically.
