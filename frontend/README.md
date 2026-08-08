# Entertainment Tracker frontend

Local React interface for the Entertainment Tracker. It uses Supabase only for
email/password authentication and sends every application-data request to the
local FastAPI API.

## Run locally

```powershell
Copy-Item .env.example .env.local
# Set NEXT_PUBLIC_API_URL and the Supabase URL/publishable key.
npm.cmd install
npm.cmd run dev
```

Open <http://localhost:3000>.

## Useful commands

```powershell
npm.cmd run lint
npm.cmd run build
npm.cmd test
```

There are no Sites, Cloudflare, D1, R2, ChatGPT authentication, or frontend
database bindings in this application.
