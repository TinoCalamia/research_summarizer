# Move & Thrive

A personalised fitness, nutrition, and recovery coach — single-user MVP for a 1-month testing phase.

The app remembers your profile (conditions, diet, goals), tracks workout sessions, surfaces flare-day swaps, and gives access to a Claude-powered coach that wears multiple hats (personal trainer, fitness guide, nutritionist, PCOS specialist, physio).

## Stack

- **Next.js 15 (App Router) + TypeScript**
- **Supabase** (Postgres + Auth via magic-link email)
- **Anthropic Claude** (server-side `/api/coach` route — API key never exposed to the browser)
- Deployed on **Vercel**

## Project layout

```
app/
  api/coach/route.ts      Server route that calls Claude with the user's profile + recent logs
  app/                    Authenticated app shell (Plan, Log, Progress, Flares, Food, Coach tabs)
  auth/callback/route.ts  Supabase OAuth callback
  login/page.tsx          Magic-link login
lib/
  supabase/               Browser, server, and middleware Supabase clients
  plan-data.ts            Static plan data (blocks, exercises, flare swaps, nutrition principles)
  types.ts                Shared types + DEFAULT_WEIGHTS seed
supabase/
  migrations/0001_initial.sql   DB schema + RLS policies + auto-create-profile trigger
middleware.ts             Auth guard: redirects unauth'd users to /login
```

## Local setup

### 1. Create a Supabase project

1. Go to https://supabase.com → New project
2. In the SQL editor, run `supabase/migrations/0001_initial.sql` to create tables, RLS policies, and triggers
3. Project Settings → API → copy the **Project URL** and the **anon public** key
4. Authentication → Providers → make sure **Email** (with magic link) is enabled
5. Authentication → URL Configuration → add `http://localhost:3000/auth/callback` and (later) your Vercel URL `https://YOUR-DEPLOY.vercel.app/auth/callback` to **Redirect URLs**

### 2. Configure env vars

Copy `.env.example` to `.env.local` and fill in:

```
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-6
NEXT_PUBLIC_SUPABASE_URL=https://YOUR_PROJECT.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=ey...
```

### 3. Install + run

```bash
npm install
npm run dev
```

Open http://localhost:3000, sign in with your email, click the magic link, and you're in.

## Deploy to Vercel

1. Push this repo to GitHub
2. https://vercel.com → New Project → import the repo
3. Add the four env vars above to Project Settings → Environment Variables
4. Deploy
5. Once you have the deployed URL, add `https://YOUR-DEPLOY.vercel.app/auth/callback` to your Supabase Auth → URL Configuration → Redirect URLs

That's it. No build configuration needed — Vercel auto-detects Next.js.

## Data model

| Table | Purpose |
|---|---|
| `profiles` | One row per auth user. Conditions, diet, goals, current week (1–4), gym weights, preferences. Auto-created on signup. |
| `session_logs` | Every logged workout: block, date, duration, mood, pain, notes, week. |
| `coach_messages` | Full chat history with the coach. |
| `coach_summaries` | Rolling summary so we don't ship 1000s of tokens of history on every coach call. (Empty in v0.1 — populate in a later iteration.) |
| `adaptations` | Coach-suggested plan tweaks surfaced on the Plan tab. |

All tables have RLS enabled — every policy is `auth.uid() = user_id`.

## Roadmap

- **v0.1 (this commit)** — Port the HTML to Next.js, server-side coach, Supabase auth + DB, deploy to Vercel
- **v0.2** — Editable profile/onboarding flow (conditions, goals, diet)
- **v0.3** — Coach summary rollup so chat history stays cheap
- **v0.4** — Meal-plan view with weekly plan + shopping list

## Open questions for the product owner

- Cycle tracking, sleep, weight log — in scope for v0.x?
- Single-user MVP only for the 1-month test — agreed
- After the test: open up to multiple users, or stay personal?
