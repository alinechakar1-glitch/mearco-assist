# MEARCO Assist 24/7 — standalone prototype (v0.1)

A small demonstrator covering login, policy entry/import, new assistance cases, simulated dispatch/status updates and an immutable append-only case-events table (within the prototype application).

## DO NOT USE FOR REAL CUSTOMERS YET

This is a training/demo starter. It has a single shared demo password, no separate operator/provider access roles, no CSRF defenses, SQLite local disk storage, no telephone/WhatsApp integration, no backups and no production privacy controls. **Do not import real policyholder data or accept real assistance requests.** It is NOT a 24/7 production service.

## Local startup

1. Install Python 3.11+.
2. `pip install -r requirements.txt`
3. Set environment variables `ADMIN_PASSWORD` (a strong private demo password) and `SESSION_SECRET` (random 32+ characters).
4. For local HTTP-only testing set `COOKIE_SECURE=0`. Leave `COOKIE_SECURE=1` on HTTPS deployments.
5. Run `uvicorn main:app --reload`.
6. Visit http://localhost:8000 and log in.

## Deploy a demo to Render

1. Create a **private GitHub repository** named `mearco-assist` and upload these files, retaining folder structure.
2. In Render create a new Web Service connected to that GitHub repository, or deploy using `render.yaml`.
3. Python build: `pip install -r requirements.txt`.
4. Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`.
5. Add `ADMIN_PASSWORD` and `SESSION_SECRET` as secret environment variables; keep `COOKIE_SECURE=1`.
6. Open the Render URL for testing with fictional data only.

**Important:** SQLite on Render without a persistent disk can be wiped on redeploy/restart. The next version must use PostgreSQL with migrations and backups before genuine data is entered. Render free web instances also spin down when idle and are not adequate for 24/7 response.

## Future phases

- PostgreSQL; users/roles; password reset/MFA; audit/security controls; CSRF; backups.
- Rule-based verified towing eligibility, detailed policy imports.
- Towing contractor portal isolated from MEARCO customer data.
- WhatsApp integration with authorized Business Platform provider.
- Hosted phone system, IVR and actual 24/7 MEARCO agent roster.
- Incident safety escalation, dispatch timers, complaint handling, notification service.
