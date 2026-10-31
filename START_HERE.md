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

## NEW: Independent production / towing imports

In **Admin & uploads** you will see two new independent upload controls:

* SWIFT production: supply `SWIFT PRD (PRD till SEP 2026)(1).xlsx` with its `PRD` tab. Imports policy number, insured, plate, dates, and mechanical-tow allowance only when explicitly expressed in Notes. Reruns update matching policy numbers. This file does **not** contain a reliable full GWP field or confirmed premium receivable balance: neither `premium` nor `due` are overwritten. Broker/customer IDs, claims, and towing history are left alone.
* Towing history: supply `MEARCO 2025-2026.xlsx`. Rows are fingerprinted to skip exact repeat imports and matched to **one** policy by normalized license plate and service date. Unmatched, cancelled, or ambiguous entries stay in a review queue. They must never be automatically attributed to a customer. Only uniquely matched mechanical towing history is deducted from the mechanical allowance. Accident towing is listed separately, because contract notes may provide unlimited accident towing.

**Deployment safety:** First deploy to a separate TEST Render service with a separate PostgreSQL database. Take a database backup before any update to a real database. The current app creates schema on import but does not include production-grade migrations. Do not upload personal/financial records before data protection, backups and access reviews. Database persistence requires PostgreSQL on Render, not ephemeral SQLite. Environment variables `ADMIN_PASSWORD` (12-72 UTF-8 bytes), `JWT_SECRET` (random 32+ bytes), and `DATABASE_URL` must be set securely. Keep the same account login you already use. Do not expose secrets or customer data in public screenshots.

**Known limitations**: Tow fingerprinting treats exact row repeats as duplicates; two truly separate calls with identical date/plate/origin/destination/phone/details need manual review. Historical matches are computed at import time; if production is uploaded again later, earlier unmatched history is not automatically rematched. The current dispatch logic still applies the mechanical allowance to all new `towing` cases, so automatic entitlement checks for accident towing are not complete and need operator review. Historical data is operational analysis, not a verified paid claim ledger. Live payment links, phone AI, and app-store publication are not connected.
