"use client"

// ============================================================
// SIDEBAR DE NAVEGAÇÃO
// components/Sidebar.tsx
// ============================================================

import { useAlertas } from "@/contexts/AlertasContext"
import { useState } from "react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import {
  LayoutDashboard, TrendingUp, ScrollText, Target,
  ShieldCheck, Bell, Coins, User, Settings,
  TrendingUpIcon, ChevronLeft, ChevronRight, LogOut,
  Crown
} from "lucide-react"

// ============================================================
// TIPOS LOCAIS
// ============================================================

type Plano = "basico" | "pro" | "enterprise"

interface Usuario {
  id: string
  email: string
  nome: string
  plano: Plano
  status: "ativo" | "inativo" | "cancelado"
  validade: string | null
  onboarding_completo: boolean
  created_at: string
}

// ============================================================
// FUNÇÃO CN (classnames) LOCAL
// ============================================================

function cn(...classes: (string | boolean | undefined | null)[]) {
  return classes.filter(Boolean).join(" ")
}

// ============================================================
// CONFIGURAÇÃO
// ============================================================

const ITENS_NAV = [
  { href: "/dashboard",     icone: LayoutDashboard, rotulo: "Dashboard",      descricao: "Visão geral e métricas" },
  { href: "/trading",       icone: TrendingUp,      rotulo: "Trading",        descricao: "Gráfico e previsões" },
  { href: "/historico",     icone: ScrollText,      rotulo: "Histórico",      descricao: "Trades realizados" },
  { href: "/performance",   icone: Target,          rotulo: "Performance",    descricao: "Acurácia por moeda" },
  { href: "/risco",         icone: ShieldCheck,     rotulo: "Gestão de Risco",descricao: "Stop-loss e take-profit" },
  { href: "/perfil",        icone: User,            rotulo: "Perfil",         descricao: "Dados e plano" },
  { href: "/configuracoes", icone: Settings,        rotulo: "Configurações",  descricao: "Preferências" },
]

const COR_PLANO: Record<Plano, string> = {
  basico: "text-cyan-400 bg-cyan-500/10 border-cyan-500/30",
  pro: "text-violet-400 bg-violet-500/10 border-violet-500/30",
  enterprise: "text-amber-400 bg-amber-500/10 border-amber-500/30",
}

const LABEL_PLANO: Record<Plano, string> = {
  basico: "Básico",
  pro: "Pro",
  enterprise: "Enterprise",
}

// ============================================================
// COMPONENTE
// ============================================================

interface SidebarProps {
  usuario: Usuario | null
}

export function Sidebar({ usuario }: SidebarProps) {
  const pathname = usePathname()
  const router = useRouter()
  const [recolhida, setRecolhida] = useState(false)
  const [saindo, setSaindo] = useState(false)
  const { alertasNaoLidos } = useAlertas()

  async function handleLogout() {
    setSaindo(true)
    try {
      // Logout simples (limpar localStorage e redirecionar)
      localStorage.removeItem("supabase.auth.token")
      router.push("/login")
    } catch {
      setSaindo(false)
    }
  }

  return (
    <aside
      className={cn(
        "flex flex-col h-screen bg-zinc-900/95 border-r border-zinc-800 sticky top-0 transition-all duration-300",
        recolhida ? "w-16" : "w-60"
      )}
    >
      {/* Logo + toggle */}
      <div className="flex items-center justify-between px-3 py-4 border-b border-zinc-800">
        {!recolhida && (
          <div className="flex items-center gap-2 min-w-0">
            <div className="flex-shrink-0 w-7 h-7 rounded-lg bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center">
              <TrendingUpIcon className="w-4 h-4 text-white" />
            </div>
            <span className="text-sm font-bold text-white truncate">TRADER AI</span>
          </div>
        )}
        {recolhida && (
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center mx-auto">
            <TrendingUpIcon className="w-4 h-4 text-white" />
          </div>
        )}
        <button
          onClick={() => setRecolhida(r => !r)}
          className={cn(
            "flex-shrink-0 text-zinc-500 hover:text-zinc-300 transition-colors p-1 rounded-lg hover:bg-zinc-800",
            recolhida && "mx-auto"
          )}
        >
          {recolhida ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Plano do usuário */}
      {usuario && (
        <div className={cn("px-3 py-3 border-b border-zinc-800", recolhida && "flex justify-center")}>
          {!recolhida ? (
            <div className={cn(
              "flex items-center gap-2 px-2.5 py-1.5 rounded-lg border text-xs font-medium",
              COR_PLANO[usuario.plano]
            )}>
              <Crown className="w-3.5 h-3.5 flex-shrink-0" />
              Plano {LABEL_PLANO[usuario.plano]}
            </div>
          ) : (
            <Crown className={cn("w-4 h-4", usuario.plano === "basico" ? "text-cyan-400" : usuario.plano === "pro" ? "text-violet-400" : "text-amber-400")} />
          )}
        </div>
      )}

      {/* Navegação */}
      <nav className="flex-1 px-2 py-3 space-y-0.5 overflow-y-auto">
        {ITENS_NAV.map(item => {
          const ativo = pathname === item.href || (item.href !== "/dashboard" && pathname?.startsWith(item.href))
          const Icone = item.icone
          // const isAlertas = item.href === "/alertas"  // ⭐ NOVO
          
          return (
            <Link
              key={item.href}
              href={item.href}
              title={recolhida ? item.rotulo : undefined}
              className={cn(
                "flex items-center gap-3 px-2 py-2 rounded-xl text-sm transition-all group relative",  // ⭐ Adicionei 'relative'
                ativo
                  ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800"
              )}
            >
              <Icone className={cn("flex-shrink-0 w-4 h-4", recolhida && "mx-auto")} />
              {!recolhida && (
                <span className="truncate font-medium">{item.rotulo}</span>
              )}
              
              
            </Link>
          )
        })}
      </nav>

      {/* Usuário + logout */}
      <div className="border-t border-zinc-800 p-3">
        {!recolhida && usuario && (
          <div className="mb-2 px-2 py-2 rounded-xl bg-zinc-800/50">
            <p className="text-xs font-medium text-zinc-300 truncate">{usuario.nome || "Usuário"}</p>
            <p className="text-[11px] text-zinc-500 truncate">{usuario.email}</p>
          </div>
        )}

        <button
          onClick={handleLogout}
          disabled={saindo}
          title={recolhida ? "Sair" : undefined}
          className={cn(
            "w-full flex items-center gap-3 px-2 py-2 rounded-xl text-sm text-zinc-500 hover:text-red-400 hover:bg-red-500/10 transition-all",
            recolhida && "justify-center"
          )}
        >
          <LogOut className="w-4 h-4 flex-shrink-0" />
          {!recolhida && <span>{saindo ? "Saindo..." : "Sair"}</span>}
        </button>
      </div>
    </aside>
  )
}