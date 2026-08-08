import vinext from "vinext";
import { defineConfig } from "vite";

// Local-only development. This frontend talks to FastAPI and Supabase Auth;
// it does not use a Sites, Cloudflare, database, or storage binding.
export default defineConfig({
  plugins: [vinext()],
  server: { host: "127.0.0.1" },
});
