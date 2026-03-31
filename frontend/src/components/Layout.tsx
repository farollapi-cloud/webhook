import { Link, Outlet, useNavigate } from "react-router-dom"
import { LogOut, LayoutDashboard } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { clearToken } from "@/lib/auth"

export function Layout() {
  const navigate = useNavigate()

  function logout() {
    clearToken()
    toast.success("Sessão encerrada")
    navigate("/login", { replace: true })
  }

  return (
    <div className="min-h-svh bg-background">
      <header className="sticky top-0 z-10 border-b border-border bg-background/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
          <div className="flex items-center gap-3">
            <Link to="/" className="flex items-center gap-2 font-semibold text-foreground">
              <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <LayoutDashboard className="h-5 w-5" />
              </span>
              Webhook SaaS
            </Link>
            <nav className="hidden text-sm text-muted-foreground sm:block">
              <Link to="/" className="hover:text-foreground">
                Empresas
              </Link>
            </nav>
          </div>
          <Button type="button" variant="outline" size="sm" onClick={logout}>
            <LogOut className="h-4 w-4" />
            Sair
          </Button>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  )
}
