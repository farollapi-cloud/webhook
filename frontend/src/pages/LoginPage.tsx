import { type FormEvent, useState } from "react"
import { Navigate, useNavigate } from "react-router-dom"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ApiError, apiJson, getApiBaseUrl } from "@/lib/api"
import { getToken, setToken } from "@/lib/auth"
import type { TokenResponse } from "@/types"

export default function LoginPage() {
  const navigate = useNavigate()
  const [clientId, setClientId] = useState("admin")
  const [clientSecret, setClientSecret] = useState("")
  const [loading, setLoading] = useState(false)

  const apiBase = getApiBaseUrl()
  const viteMissing =
    import.meta.env.PROD && (!import.meta.env.VITE_API_URL || String(import.meta.env.VITE_API_URL).trim() === "")
  const looksLikeLocalhostInProd =
    import.meta.env.PROD && (apiBase.includes("localhost") || apiBase.includes("127.0.0.1"))

  if (getToken()) {
    return <Navigate to="/" replace />
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      const data = await apiJson<TokenResponse>("/api/v1/auth/token", {
        method: "POST",
        body: JSON.stringify({ client_id: clientId, client_secret: clientSecret }),
        skipAuth: true,
      })
      setToken(data.access_token)
      toast.success("Login realizado")
      navigate("/", { replace: true })
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 0) {
          toast.error(
            `Sem conexão com a API (${apiBase}). No Render: no Static Site defina VITE_API_URL com a URL https da Web Service da API e faça redeploy. Na API, defina CORS_ORIGINS com a URL deste site.`,
            { duration: 12000 },
          )
        } else {
          toast.error("Credenciais inválidas ou API indisponível")
        }
      } else {
        toast.error("Falha ao conectar")
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-svh items-center justify-center bg-muted/30 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Entrar</CardTitle>
          <CardDescription>
            Use o <code className="rounded bg-muted px-1 py-0.5 text-xs">client_id</code> e{" "}
            <code className="rounded bg-muted px-1 py-0.5 text-xs">client_secret</code> configurados na API
            (variáveis <code className="text-xs">AUTH_CLIENT_ID</code> e{" "}
            <code className="text-xs">AUTH_CLIENT_SECRET</code> no Web Service).
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {(viteMissing || looksLikeLocalhostInProd) && (
            <div className="rounded-lg border border-amber-500/50 bg-amber-500/10 px-3 py-2 text-sm text-amber-900 dark:text-amber-100">
              <strong>Configuração do Static Site:</strong> este build não tem{" "}
              <code className="text-xs">VITE_API_URL</code> apontando para a API na internet. No Render, em
              Environment do <strong>Static Site</strong>, adicione{" "}
              <code className="text-xs">VITE_API_URL=https://(sua-api).onrender.com</code> e faça um novo deploy.
            </div>
          )}
          <p className="text-xs text-muted-foreground">
            Chamadas vão para: <code className="break-all rounded bg-muted px-1 py-0.5">{apiBase}</code>
          </p>
          <form onSubmit={onSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="client_id">Client ID</Label>
              <Input
                id="client_id"
                autoComplete="username"
                value={clientId}
                onChange={(e) => setClientId(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="client_secret">Client secret</Label>
              <Input
                id="client_secret"
                type="password"
                autoComplete="current-password"
                value={clientSecret}
                onChange={(e) => setClientSecret(e.target.value)}
                required
              />
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Entrando…" : "Entrar"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
