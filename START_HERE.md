# MEARCO ASSIST ONE V2 — START HERE

This is a **NEW replacement implementation with a similar appearance**, not a copy of the lost MEARCO Assist v0.7 code. One FastAPI backend runs the web dashboard and the Expo mobile client. **Do not deploy over existing live services or databases before review and backups.**

## 1. Create a NEW GitHub repository
Unzip all contents, upload everything to a new repository, keeping `backend/`, `mobile/`, `sample/`, `tests/`, and `render.yaml` at repository root.

## 2. Create a NEW Render service
Choose Blueprint from the new repository and approve **one new web service and one new PostgreSQL database** defined in render.yaml. Set a durable `JWT_SECRET` (the blueprint generates one). Deploy. Verify `/health`, then open `/` to see the teal MEARCO Assist command center.

## 3. Provision pilot logins
Render shell access may depend on plan. Prefer local testing first: `cd backend && pip install -r requirements.txt && python seed_demo.py`, then `uvicorn main:app --reload`. Record the unique demo credentials printed by seed_demo.py. Deploy sample users in staging only, never in production.

## 4. Import sample Excel
Sign in as the demo admin, select **Admin & uploads**, import `sample/MEARCO_ONE_TEST_DATA.xlsx`. Test **Policies → Tow balances → Assistance & claims → Dispatch portal → Providers → Unpaid premiums → Payment requests**. Everything is fictional.

## 5. Mobile apps
`cd mobile && npm install && EXPO_PUBLIC_API_URL=https://YOUR-RENDER-URL npx expo start`. Use Expo Go/dev builds for testing. Apple Store and Google Play require developer accounts, signing assets, privacy policy, testing, EAS builds, and review. This zip does **not** contain an installed/store-published app.

## 6. Not yet live
Phone AI, WhatsApp, push alerts, real garage quotes, policy PDFs, online Whish/Monty/bank checkout, accounting integration, broker commissions, secure production onboarding, 24/7 dispatch SLA, and push notifications require further development or provider credentials. No live payments are captured; the payment request API creates **pending records only**. Emergency calls must be answered by people until a properly tested call flow exists.
