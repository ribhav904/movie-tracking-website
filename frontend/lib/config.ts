import { z } from "zod";

const configSchema = z.object({
  // Accept either a direct API URL for local development or a same-origin
  // path that Vercel rewrites to the FastAPI service in production.
  NEXT_PUBLIC_API_URL: z.string().min(1).optional(),
  NEXT_PUBLIC_SUPABASE_URL: z.string().url().optional(),
  NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY: z.string().min(1).optional(),
});

export const frontendConfig = configSchema.parse({
  NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
  NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY: process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY,
});

export const isBackendConfigured = Boolean(frontendConfig.NEXT_PUBLIC_API_URL);
export const isSupabaseConfigured = Boolean(
  frontendConfig.NEXT_PUBLIC_SUPABASE_URL && frontendConfig.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY,
);
