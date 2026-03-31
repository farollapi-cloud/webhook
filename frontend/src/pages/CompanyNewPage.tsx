import { type FormEvent, useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { ArrowLeft } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { ApiError, apiJson } from "@/lib/api"
import type { Company } from "@/types"

export default function CompanyNewPage() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const form = new FormData(e.currentTarget)
    const legal_name = String(form.get("legal_name") ?? "")
    const contact_name = String(form.get("contact_name") ?? "")
    const email = String(form.get("email") ?? "")
    const phone = String(form.get("phone") ?? "")
    const status = String(form.get("status") ?? "active")
    const notesRaw = form.get("notes")
    const notes = notesRaw ? String(notesRaw) : null

    setLoading(true)
    try {
      const created = await apiJson<Company>("/api/v1/companies", {
        method: "POST",
        body: JSON.stringify({
          legal_name,
          contact_name,
          email,
          phone,
          status,
          notes,
        }),
      })
      toast.success("Empresa criada")
      navigate(`/companies/${created.id}`, { replace: true })
    } catch (err) {
      if (err instanceof ApiError) toast.error("Não foi possível criar a empresa")
      else toast.error("Erro de rede")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <Button variant="ghost" size="sm" asChild>
          <Link to="/">
            <ArrowLeft className="h-4 w-4" />
            Voltar
          </Link>
        </Button>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Nova empresa</CardTitle>
          <CardDescription>Preencha os dados cadastrais.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2 sm:col-span-2">
                <Label htmlFor="legal_name">Razão social / nome</Label>
                <Input id="legal_name" name="legal_name" required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="contact_name">Responsável</Label>
                <Input id="contact_name" name="contact_name" required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">E-mail</Label>
                <Input id="email" name="email" type="email" required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="phone">Telefone</Label>
                <Input id="phone" name="phone" required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="status">Status</Label>
                <select
                  id="status"
                  name="status"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  defaultValue="active"
                >
                  <option value="active">active</option>
                  <option value="inactive">inactive</option>
                  <option value="suspended">suspended</option>
                </select>
              </div>
              <div className="space-y-2 sm:col-span-2">
                <Label htmlFor="notes">Observações</Label>
                <Textarea id="notes" name="notes" rows={3} />
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button type="button" variant="outline" asChild>
                <Link to="/">Cancelar</Link>
              </Button>
              <Button type="submit" disabled={loading}>
                {loading ? "Salvando…" : "Salvar"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
