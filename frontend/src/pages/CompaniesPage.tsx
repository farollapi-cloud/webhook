import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { Building2, Plus } from "lucide-react"
import { toast } from "sonner"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ApiError, apiJson } from "@/lib/api"
import type { Company } from "@/types"

const statusVariant: Record<Company["status"], "success" | "secondary" | "warning"> = {
  active: "success",
  inactive: "secondary",
  suspended: "warning",
}

export default function CompaniesPage() {
  const [rows, setRows] = useState<Company[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const data = await apiJson<Company[]>("/api/v1/companies")
        if (!cancelled) setRows(data)
      } catch (e) {
        if (!cancelled) {
          if (e instanceof ApiError) toast.error("Não foi possível carregar empresas")
          else toast.error("Erro de rede")
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Empresas</h1>
          <p className="text-sm text-muted-foreground">Gerencie empresas e números WhatsApp (Uazapi).</p>
        </div>
        <Button asChild>
          <Link to="/companies/new">
            <Plus className="h-4 w-4" />
            Nova empresa
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Lista</CardTitle>
          <CardDescription>Clique em uma empresa para ver números e webhooks.</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-sm text-muted-foreground">Carregando…</p>
          ) : rows.length === 0 ? (
            <p className="text-sm text-muted-foreground">Nenhuma empresa cadastrada.</p>
          ) : (
            <ul className="divide-y divide-border rounded-lg border border-border">
              {rows.map((c) => (
                <li key={c.id}>
                  <Link
                    to={`/companies/${c.id}`}
                    className="flex flex-col gap-2 px-4 py-4 transition-colors hover:bg-muted/50 sm:flex-row sm:items-center sm:justify-between"
                  >
                    <div className="flex items-start gap-3">
                      <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                        <Building2 className="h-4 w-4" />
                      </span>
                      <div>
                        <p className="font-medium">{c.legal_name}</p>
                        <p className="text-sm text-muted-foreground">{c.email}</p>
                      </div>
                    </div>
                    <Badge variant={statusVariant[c.status]}>{c.status}</Badge>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
