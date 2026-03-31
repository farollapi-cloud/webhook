import { type FormEvent, useState } from "react"
import { Navigate, useNavigate } from "react-router-dom"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ApiError, apiJson } from "@/lib/api"
import { getToken, setToken } from "@/lib/auth"
import type { TokenResponse } from "@/types"

export default function LoginPage() {
  const navigate = useNavigate()
  const [clientId, setClientId] = useState("admin")
  const [clientSecret, setClientSecret] = useState("")
  const [loading, setLoading] = useState(false)

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
        toast.error("Credenciais inválidas ou API indisponível")
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
            <code className="rounded bg-muted px-1 py-0.5 text-xs">client_secret</code> configurados na API.
          </CardDescription>
        </CardHeader>
        <CardContent>
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
