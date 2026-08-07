import { frontendConfig, isBackendConfigured } from "@/lib/config";
import { getDemoResponse } from "@/lib/demo-data";
import { getSupabaseClient } from "@/lib/supabase";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly code?: string,
  ) {
    super(message);
  }
}

export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  if (!isBackendConfigured) return getDemoResponse(path) as T;

  const session = await getSupabaseClient()?.auth.getSession();
  const token = session?.data.session?.access_token;
  const response = await fetch(`${frontendConfig.NEXT_PUBLIC_API_URL}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      ...(init.body ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init.headers,
    },
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new ApiError(
      payload?.error?.message ?? "The request could not be completed.",
      response.status,
      payload?.error?.code,
    );
  }
  return response.status === 204 ? (undefined as T) : ((await response.json()) as T);
}
