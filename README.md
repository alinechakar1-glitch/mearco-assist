# MEARCO Assist 24/7 — complete clean demo (v0.4.1 bundle)

This is a **testing-only** standalone website application. It includes the customer-facing chat simulator, employee dashboard, policy demo import, case details, and provider dispatch demo. It **does not connect to WhatsApp**, telephone systems, live towing, or emergency response.

## Folder structure
- `main.py`, `requirements.txt`, `render.yaml`, `.gitignore`, `README.md` at repository root.
- All `.html` files **inside `templates/`**.
- `chat.js`, `style.css`, and `policy_template.csv` **inside `static/`**.
- **Never upload** `*.sqlite3` or real policy/customer data to a public repository.

## Updating your existing GitHub repository
1. Download and extract this ZIP. **Upload the contents, not the ZIP or an outer folder.**
2. For a clean replacement, remove old duplicate `.html`, `.css`, `.js` files mistakenly placed at repository root. Do not remove or recreate the GitHub repository.
3. Upload the files with `templates/` and `static/` preserved. Confirm that `templates/chat.html` and `static/chat.js` exist on GitHub; do not leave copies at repository root.
4. Commit to `main`, let your existing Render service deploy. Keep your current Render environment secrets.
5. Open `/version`, `/chat`, and `/login` on the deployed site.

## Render settings
- Build: `pip install -r requirements.txt`
- Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Private env vars: `ADMIN_PASSWORD` and `SESSION_SECRET` are required. `PROVIDER_PASSWORD` is optional for demo provider login.
- `PUBLIC_INTAKE_ENABLED=0` and `PUBLIC_TRACKING_ENABLED=0` (leave disabled).

## Testing
- `/chat`: browser-based simulated conversation; only fictional case choices; the test case may appear in the staff dashboard.
- `/login`: staff demo login. `/`: dashboard after sign-in.
- `/assist`: public placeholder. `/provider/login`: provider demo login.
- Test data is in local SQLite and **may disappear on Render restart or redeployment**. There are no durable notifications, reliable queues, external messaging, or live call-center coverage.

**Safety:** Do not distribute as an active assistance/emergency service or collect genuine personal information until persistent storage, operator response, permissions, privacy and security have been implemented and tested.
