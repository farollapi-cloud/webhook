import { clearToken, getToken } from "./auth"

/** URL base da API (definida no *build* do Static Site com VITE_API_URL). */
export function getApiBaseUrl(): string {
  const u = import.meta.env.VITE_API_URL as string | undefined
  return (u ?? "http://localhost:8000").replace(/\/$/, "")
}

function buildUrl(path: string): string {
  const base = getApiBaseUrl()
  const p = path.startsWith("/") ? path : `/${path}`
  return `${base}${p}`
}

export class ApiError extends Error {
  status: number
  body: string

  constructor(status: number, body: string) {
    super(body || `HTTP ${status}`)
    this.status = status
    this.body = body
  }
}

export async function apiJson<T>(
  path: string,
  options: RequestInit & { skipAuth?: boolean } = {},
): Promise<T> {
  const url = buildUrl(path)
  const headers = new Headers(options.headers)
  if (!headers.has("Content-Type") && options.body && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json")
  }
  if (!options.skipAuth) {
    const t = getToken()
    if (t) headers.set("Authorization", `Bearer ${t}`)
  }

  let res: Response
  try {
    res = await fetch(url, { ...options, headers })
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e)
    throw new ApiError(0, msg)
  }

  const text = await res.text()
  if (res.status === 401) {
    clearToken()
  }
  if (!res.ok) {
    throw new ApiError(res.status, text)
  }
  if (!text) return undefined as T
  return JSON.parse(text) as T
}
