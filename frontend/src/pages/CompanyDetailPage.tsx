import { type FormEvent, useCallback, useEffect, useState } from "react"
import { Link, useParams } from "react-router-dom"
import { ArrowLeft, Copy, RefreshCw, Smartphone } from "lucide-react"
import { toast } from "sonner"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { ApiError, apiJson } from "@/lib/api"
import type { Company, PhoneNumber, WebhookRegenerateResponse } from "@/types"

export default function CompanyDetailPage() {
  const { id } = useParams<{ id: string }>()
  const companyId = id ?? ""

  const [company, setCompany] = useState<Company | null>(null)
  const [phones, setPhones] = useState<PhoneNumber[]>([])
  const [loading, setLoading] = useState(true)
  const [savingCompany, setSavingCompany] = useState(false)
  const [addingPhone, setAddingPhone] = useState(false)
  const [regenId, setRegenId] = useState<string | null>(null)

  const load = useCallback(async () => {
    if (!companyId) return
    const [c, p] = await Promise.all([
      apiJson<Company>(`/api/v1/companies/${companyId}`),
      apiJson<PhoneNumber[]>(`/api/v1/companies/${companyId}/phone-numbers`),
    ])
    setCompany(c)
    setPhones(p)
  }, [companyId])

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      if (!companyId) return
      setLoading(true)
      try {
        await load()
      } catch (e) {
        if (!cancelled) {
          if (e instanceof ApiError) toast.error("Empresa não encontrada ou sem permissão")
          else toast.error("Erro de rede")
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [companyId, load])

  async function onSaveCompany(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    if (!company) return
    const form = new FormData(e.currentTarget)
    setSavingCompany(true)
    try {
      const updated = await apiJson<Company>(`/api/v1/companies/${company.id}`, {
        method: "PATCH",
        body: JSON.stringify({
          legal_name: String(form.get("legal_name") ?? ""),
          contact_name: String(form.get("contact_name") ?? ""),
          email: String(form.get("email") ?? ""),
          phone: String(form.get("phone") ?? ""),
          status: String(form.get("status") ?? "active"),
          notes: form.get("notes") ? String(form.get("notes")) : null,
        }),
      })
      setCompany(updated)
      toast.success("Empresa atualizada")
    } catch {
      toast.error("Falha ao salvar empresa")
    } finally {
      setSavingCompany(false)
    }
  }

  async function onAddPhone(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const form = new FormData(e.currentTarget)
    setAddingPhone(true)
    try {
      const created = await apiJson<PhoneNumber>(`/api/v1/companies/${companyId}/phone-numbers`, {
        method: "POST",
        body: JSON.stringify({
          label: String(form.get("label") ?? ""),
          phone_e164: String(form.get("phone_e164") ?? ""),
          provider: "uazapi",
          uazapi_base_url: String(form.get("uazapi_base_url") ?? ""),
          uazapi_instance_token: String(form.get("uazapi_instance_token") ?? ""),
          connection_status: String(form.get("connection_status") ?? "active"),
        }),
      })
      setPhones((prev) => [created, ...prev])
      e.currentTarget.reset()
      if (created.webhook_url) {
        toast.success("Número criado — copie a URL do webhook na Uazapi")
      } else {
        toast.success("Número criado")
      }
    } catch {
      toast.error("Não foi possível criar o número (verifique E.164 e duplicatas)")
    } finally {
      setAddingPhone(false)
    }
  }

  async function copyText(text: string) {
    try {
      await navigator.clipboard.writeText(text)
      toast.success("Copiado")
    } catch {
      toast.error("Não foi possível copiar")
    }
  }

  async function regenerate(phoneId: string) {
    setRegenId(phoneId)
    try {
      const res = await apiJson<WebhookRegenerateResponse>(
        `/api/v1/companies/${companyId}/phone-numbers/${phoneId}/webhook/regenerate`,
        { method: "POST" },
      )
      toast.message("Webhook regenerado", {
        description: "Atualize a URL no painel da Uazapi.dev",
      })
      await copyText(res.webhook_url)
      setPhones((prev) =>
        prev.map((p) =>
          p.id === phoneId ? { ...p, webhook_url: null, webhook_url_prefix: p.webhook_url_prefix } : p,
        ),
      )
    } catch {
      toast.error("Falha ao regenerar webhook")
    } finally {
      setRegenId(null)
    }
  }

  if (!companyId) {
    return <p className="text-sm text-muted-foreground">ID inválido</p>
  }

  if (loading || !company) {
    return <p className="text-sm text-muted-foreground">Carregando…</p>
  }

  return (
    <div className="space-y-8">
      <div>
        <Button variant="ghost" size="sm" asChild>
          <Link to="/">
            <ArrowLeft className="h-4 w-4" />
            Empresas
          </Link>
        </Button>
      </div>

      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{company.legal_name}</h1>
        <p className="text-sm text-muted-foreground">{company.email}</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Dados da empresa</CardTitle>
          <CardDescription>Alterações aqui não alteram o token do webhook.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSaveCompany} className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2 sm:col-span-2">
                <Label htmlFor="legal_name">Razão social / nome</Label>
                <Input id="legal_name" name="legal_name" defaultValue={company.legal_name} required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="contact_name">Responsável</Label>
                <Input id="contact_name" name="contact_name" defaultValue={company.contact_name} required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">E-mail</Label>
                <Input id="email" name="email" type="email" defaultValue={company.email} required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="phone">Telefone</Label>
                <Input id="phone" name="phone" defaultValue={company.phone} required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="status">Status</Label>
                <select
                  id="status"
                  name="status"
                  defaultValue={company.status}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <option value="active">active</option>
                  <option value="inactive">inactive</option>
                  <option value="suspended">suspended</option>
                </select>
              </div>
              <div className="space-y-2 sm:col-span-2">
                <Label htmlFor="notes">Observações</Label>
                <Textarea id="notes" name="notes" rows={3} defaultValue={company.notes ?? ""} />
              </div>
            </div>
            <div className="flex justify-end">
              <Button type="submit" disabled={savingCompany}>
                {savingCompany ? "Salvando…" : "Salvar empresa"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Novo número WhatsApp</CardTitle>
          <CardDescription>
            E.164 obrigatório (ex. <code className="text-xs">+5511999999999</code>). Na criação, a URL completa do
            webhook é exibida uma vez.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onAddPhone} className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="label">Nome de identificação</Label>
              <Input id="label" name="label" placeholder="Vendas" required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="phone_e164">Número (E.164)</Label>
              <Input id="phone_e164" name="phone_e164" placeholder="+5511999999999" required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="connection_status">Status da conexão</Label>
              <select
                id="connection_status"
                name="connection_status"
                defaultValue="active"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="active">active</option>
                <option value="inactive">inactive</option>
                <option value="pending">pending</option>
                <option value="error">error</option>
              </select>
            </div>
            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="uazapi_base_url">URL base Uazapi</Label>
              <Input id="uazapi_base_url" name="uazapi_base_url" placeholder="https://..." required />
            </div>
            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="uazapi_instance_token">Token / credencial da instância Uazapi</Label>
              <Input id="uazapi_instance_token" name="uazapi_instance_token" type="password" required />
            </div>
            <div className="sm:col-span-2 flex justify-end">
              <Button type="submit" disabled={addingPhone}>
                {addingPhone ? "Criando…" : "Adicionar número"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <div className="space-y-4">
        <h2 className="text-lg font-semibold">Números e webhooks</h2>
        {phones.length === 0 ? (
          <p className="text-sm text-muted-foreground">Nenhum número cadastrado.</p>
        ) : (
          <ul className="space-y-4">
            {phones.map((p) => (
              <li key={p.id}>
                <Card>
                  <CardHeader className="flex flex-row items-start justify-between gap-4 space-y-0">
                    <div className="space-y-1">
                      <CardTitle className="text-base">{p.label}</CardTitle>
                      <CardDescription className="font-mono text-xs">{p.phone_e164}</CardDescription>
                    </div>
                    <Badge variant="outline">{p.connection_status}</Badge>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div>
                      <p className="text-xs font-medium text-muted-foreground">Prefixo do webhook (token oculto)</p>
                      <div className="mt-1 flex flex-col gap-2 sm:flex-row sm:items-center">
                        <code className="block flex-1 break-all rounded-md border border-border bg-muted/50 px-2 py-1.5 text-xs">
                          {p.webhook_url_prefix}
                        </code>
                        <Button type="button" variant="outline" size="sm" onClick={() => copyText(p.webhook_url_prefix)}>
                          <Copy className="h-4 w-4" />
                          Copiar prefixo
                        </Button>
                      </div>
                    </div>
                    {p.webhook_url ? (
                      <div>
                        <p className="text-xs font-medium text-emerald-600 dark:text-emerald-400">
                          URL completa (exibida só na criação)
                        </p>
                        <div className="mt-1 flex flex-col gap-2 sm:flex-row sm:items-center">
                          <code className="block flex-1 break-all rounded-md border border-border bg-muted/50 px-2 py-1.5 text-xs">
                            {p.webhook_url}
                          </code>
                          <Button type="button" size="sm" onClick={() => copyText(p.webhook_url!)}>
                            <Smartphone className="h-4 w-4" />
                            Copiar URL
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <p className="text-xs text-muted-foreground">
                        O token secreto não é reexibido. Use <strong>Regenerar</strong> para obter uma nova URL completa e
                        atualize na Uazapi.dev.
                      </p>
                    )}
                    <div className="flex flex-wrap gap-2 pt-1">
                      <Button
                        type="button"
                        variant="secondary"
                        size="sm"
                        disabled={regenId === p.id}
                        onClick={() => regenerate(p.id)}
                      >
                        <RefreshCw className="h-4 w-4" />
                        {regenId === p.id ? "Regenerando…" : "Regenerar webhook"}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
