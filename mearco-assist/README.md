# MEARCO Assist v0.7 — Operations Dashboard and Staff Accounts

Complete upgrade over v0.6: management dashboard, dashboard test alerts, production and towing Excel/CSV import, vehicle-level entitlement tracking, manual tow recording, case management, provider portal, chatbot test, staff accounts and administrator account management.

## Deployment
Upload the **contents of this folder** to the existing GitHub repository, preserving `templates/` and `static/`. Keep the existing Render service and set `ADMIN_PASSWORD` and `SESSION_SECRET` as secrets. Then open `/version` (0.7.0), `/login`, `/users` (admin), `/vehicle-usage`, and `/chat`.

## Permissions
Admin logs in with the Render `ADMIN_PASSWORD`, then visits `/users` and creates named operator/supervisor accounts. Staff sign in via username/password. Passwords use PBKDF2-HMAC-SHA256 hashes with individual salts. Admin can disable accounts or reset passwords. Staff-user changes are logged. **Limitations:** existing sessions are not invalidated immediately when an account is disabled; operator and supervisor currently share operational access, including imports. This is not yet a production-hardened identity system (no MFA, lockout, password self-service, or granular import permissions).

## Import rules
Daily production imports upsert matching policy+vehicle+term records. Tow logs use reference-based deduplication. Only `Completed` counts toward allowance; cancelled/pending do not. Ambiguous matches and missing limits require review. Upload sample files from `static/`. Verify actual contractual allowances before live use.

## Production blockers — do not upload personal client information yet
**This release uses SQLite at `DB_PATH`. Standard Render web instances have ephemeral local storage, so real uploads and staff accounts may be lost on restart or redeployment.** Before real data: persistent Postgres-backed implementation and migration; data backups/restore tests; identity hardening and permissions; compliance/legal review; monitoring; tested 24/7 on-call escalation and telephony/WhatsApp service integrations. No actual WhatsApp bot, telephone hotline, live dispatch or emergency response is connected. `PUBLIC_INTAKE_ENABLED=0` must remain unchanged until all release gates pass.

## Developer smoke tests
Use environment variables `ADMIN_PASSWORD`, `SESSION_SECRET` and `COOKIE_SECURE=0` for local http-only testing. Run `uvicorn main:app --reload`. Do not commit SQLite files, tokens, or real data.
