import { createClient, type SupabaseClient } from "@supabase/supabase-js";

import { frontendConfig, isSupabaseConfigured } from "@/lib/config";

let client: SupabaseClient | null = null;

export function getSupabaseClient(): SupabaseClient | null {
  if (!isSupabaseConfigured) return null;
  if (!client) {
    client = createClient(
      frontendConfig.NEXT_PUBLIC_SUPABASE_URL!,
      frontendConfig.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!,
    );
  }
  return client;
}
