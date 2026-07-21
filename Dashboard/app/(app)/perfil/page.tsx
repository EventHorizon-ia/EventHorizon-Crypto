"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import {
  User, Mail, Crown, Calendar, TrendingUp,
  Target, Activity, Zap, LogOut, Shield,
  Clock, Loader2, Edit2, Check, X, AlertTriangle
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { supabase, getUser, logout } from "@/lib/supabase-client"
import { API_BASE_URL } from "@/lib/api"

// ============================================
// TIPOS
// ============================================

interface PerfilUsuario {
  id: string
  nome: string
  email: string
  plano: string
  status: string
  created_at: string
  onboarding_completo: boolean
}

interface Estatisticas {
  total_moedas: number
  total_verificacoes: number
  acuracia_media: number
  melhor_moeda: string | null
}

// ============================================
// COMPONENTE
// ============================================

export default function PerfilPage() {
  const router = useRouter()
  const [perfil, setPerfil] = useState<PerfilUsuario | null>(null)
  const [stats, setStats] = useState<Estatisticas>({
    total_moedas: 0,
    total_verificacoes: 0,
    acuracia_media: 0,
    melhor_moeda: null
  })
  const [loading, setLoading] = useState(true)
  const [saindo, setSaindo] = useState(false)
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false)
  
  // Editar nome
  const [editandoNome, setEditandoNome] = useState(false)
  const [novoNome, setNovoNome] = useState("")
  const [salvandoNome, setSalvandoNome] = useState(false)

  useEffect(() => {
    carregarPerfil()
    carregarStats()
  }, [])

  async function carregarPerfil() {
    try {
      const user = await getUser()
      if (!user) {
        router.replace("/login")
        return
      }

      const { data, error } = await supabase
        .from("perfis")
        .select("*")
        .eq("user_id", user.id)
        .single()

      if (error || !data) {
        router.replace("/login")
        return
      }

      setPerfil({
        id: user.id,
        nome: data.nome || "Usuário",
        email: user.email || "",
        plano: data.plano || "basico",
        status: data.status || "ativo",
        created_at: data.created_at || new Date().toISOString(),
        onboarding_completo: data.onboarding_completo || false
      })
      setNovoNome(data.nome || "")
    } catch (e) {
      console.error("Erro ao carregar perfil:", e)
    } finally {
      setLoading(false)
    }
  }

  async function carregarStats() {
    try {
      const res = await fetch(`${API_BASE_URL}/dashboard/realtime`)
      const data = await res.json()
      
      if (data.moedas) {
        const acuracias = data.moedas
          .filter((m: any) => m.acuracias_reais && Object.keys(m.acuracias_reais).length > 0)
          .map((m: any) => {
            const accs = Object.values(m.acuracias_reais) as any[]
            const media = accs.reduce((sum: number, a: any) => sum + a.acuracia, 0) / accs.length
            return { symbol: m.symbol, acuracia: media }
          })

        setStats({
          total_moedas: data.total_moedas || 0,
          total_verificacoes: data.total_verificacoes || 0,
          acuracia_media: acuracias.length > 0 
            ? Math.round(acuracias.reduce((s: number, a: any) => s + a.acuracia, 0) / acuracias.length) 
            : 0,
          melhor_moeda: acuracias.length > 0 
            ? acuracias.sort((a: any, b: any) => b.acuracia - a.acuracia)[0].symbol 
            : null
        })
      }
    } catch (e) {
      console.error("Erro ao carregar stats:", e)
    }
  }

  async function salvarNome() {
    if (!perfil || !novoNome.trim()) return
    setSalvandoNome(true)
    
    try {
      await supabase
        .from("perfis")
        .update({ nome: novoNome.trim() })
        .eq("user_id", perfil.id)
      
      setPerfil({ ...perfil, nome: novoNome.trim() })
      setEditandoNome(false)
    } catch (e) {
      console.error("Erro ao salvar nome:", e)
    } finally {
      setSalvandoNome(false)
    }
  }

  async function handleLogout() {
    setSaindo(true)
    try {
      await logout()
      localStorage.removeItem("supabase.auth.token")
      localStorage.removeItem("trader_loaded_coins")
      localStorage.removeItem("trader_is_running")
      router.push("/login")
    } catch {
      setSaindo(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-4rem)]">
        <Loader2 className="w-8 h-8 animate-spin text-cyan-400" />
      </div>
    )
  }

  if (!perfil) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-4rem)]">
        <p className="text-muted-foreground">Erro ao carregar perfil</p>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6 max-w-2xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Meu Perfil</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Gerencie sua conta e visualize suas estatísticas
        </p>
      </div>

      {/* Card do Usuário */}
      <div className="rounded-xl border border-border/50 bg-secondary/10 p-6">
        <div className="flex items-center gap-4 mb-6">
          {/* Avatar */}
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-white text-2xl font-bold flex-shrink-0">
            {perfil.nome?.charAt(0)?.toUpperCase() || "U"}
          </div>
          
          <div className="flex-1 min-w-0">
            {/* Nome editável */}
            {editandoNome ? (
              <div className="flex items-center gap-2 mb-1">
                <input
                  type="text"
                  value={novoNome}
                  onChange={e => setNovoNome(e.target.value)}
                  className="bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-1.5 text-white text-lg font-bold w-full focus:outline-none focus:border-cyan-500"
                  autoFocus
                  onKeyDown={e => { if (e.key === "Enter") salvarNome(); if (e.key === "Escape") setEditandoNome(false) }}
                />
                <button onClick={salvarNome} disabled={salvandoNome} className="text-green-400 hover:text-green-300">
                  {salvandoNome ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                </button>
                <button onClick={() => setEditandoNome(false)} className="text-zinc-500 hover:text-zinc-300">
                  <X className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2 mb-1">
                <h2 className="text-xl font-bold truncate">{perfil.nome}</h2>
                <button onClick={() => { setNovoNome(perfil.nome); setEditandoNome(true) }} className="text-zinc-500 hover:text-cyan-400 transition-colors">
                  <Edit2 className="w-3.5 h-3.5" />
                </button>
              </div>
            )}
            
            <p className="text-sm text-muted-foreground truncate flex items-center gap-1">
              <Mail className="w-3.5 h-3.5" />
              {perfil.email}
            </p>
            <div className="flex items-center gap-2 mt-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-medium border bg-cyan-500/10 text-cyan-400 border-cyan-500/30">
                <Crown className="w-3 h-3 inline mr-1" />
                Plano Básico
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-500/10 text-green-400 border border-green-500/20">
                {perfil.status === "ativo" ? "Ativo" : "Inativo"}
              </span>
            </div>
          </div>
        </div>

        {/* Info */}
        <div className="grid grid-cols-2 gap-3 mb-6">
          {[
            { label: "Membro desde", value: new Date(perfil.created_at).toLocaleDateString("pt-BR"), icon: Calendar },
            { label: "Plano atual", value: "Básico (Grátis)", icon: Crown },
          ].map((info, i) => (
            <div key={i} className="rounded-lg bg-secondary/20 p-3">
              <div className="flex items-center gap-1.5 mb-1">
                <info.icon className="w-3.5 h-3.5 text-muted-foreground" />
                <span className="text-[10px] text-muted-foreground uppercase tracking-wider">{info.label}</span>
              </div>
              <p className="text-sm font-medium">{info.value}</p>
            </div>
          ))}
        </div>

        {/* Botão Sair */}
        <Button 
          onClick={() => setShowLogoutConfirm(true)} 
          disabled={saindo} 
          variant="outline" 
          className="w-full"
        >
          <LogOut className="w-4 h-4 mr-2" />
          {saindo ? "Saindo..." : "Sair da conta"}
        </Button>
      </div>

      {/* Modal de confirmação de saída */}
      {showLogoutConfirm && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
          <div className="bg-zinc-900 rounded-2xl p-6 w-96 border border-zinc-800 shadow-2xl">
            <div className="text-center mb-4">
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-amber-500/10 border border-amber-500/30 mb-3">
                <AlertTriangle className="w-6 h-6 text-amber-400" />
              </div>
              <h3 className="text-lg font-bold text-white">Sair da conta?</h3>
              <p className="text-sm text-zinc-400 mt-1">Você precisará fazer login novamente para acessar.</p>
            </div>
            <div className="flex gap-2">
              <Button onClick={() => setShowLogoutConfirm(false)} variant="outline" className="flex-1">
                Cancelar
              </Button>
              <Button onClick={handleLogout} className="flex-1 bg-red-500/20 border border-red-500/30 text-red-400 hover:bg-red-500/30">
                <LogOut className="w-4 h-4 mr-2" />
                Sair
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Estatísticas */}
      <div className="rounded-xl border border-border/50 bg-secondary/10 p-6">
        <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-cyan-400" />
          Minhas Estatísticas
        </h3>
        
        <div className="grid grid-cols-2 gap-3">
          {[
            { label: "Moedas Ativas", value: stats.total_moedas, icon: Zap, color: "text-yellow-400", bg: "bg-yellow-500/10 border-yellow-500/20" },
            { label: "Trades Verificados", value: stats.total_verificacoes.toLocaleString(), icon: Activity, color: "text-cyan-400", bg: "bg-cyan-500/10 border-cyan-500/20" },
            { label: "Acurácia Média", value: `${stats.acuracia_media}%`, icon: Target, color: "text-green-400", bg: "bg-green-500/10 border-green-500/20" },
            { label: "Melhor Moeda", value: stats.melhor_moeda || "—", icon: Shield, color: "text-purple-400", bg: "bg-purple-500/10 border-purple-500/20" },
          ].map((card, i) => (
            <div key={i} className={cn("rounded-lg p-3 border", card.bg)}>
              <div className="flex items-center gap-1.5 mb-1">
                <card.icon className={cn("w-3.5 h-3.5", card.color)} />
                <span className="text-[10px] text-muted-foreground">{card.label}</span>
              </div>
              <p className={cn("text-lg font-bold", card.color)}>{card.value}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Atividade Recente */}
      <div className="rounded-xl border border-border/50 bg-secondary/10 p-6">
        <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
          <Clock className="w-5 h-5 text-cyan-400" />
          Atividade
        </h3>
        
        <div className="space-y-2">
          {[
            { texto: "Conta criada", data: new Date(perfil.created_at).toLocaleDateString("pt-BR"), icon: Calendar },
            { texto: "Onboarding completo", data: perfil.onboarding_completo ? "Sim" : "Não", icon: Check },
            { texto: "Último acesso", data: new Date().toLocaleDateString("pt-BR"), icon: Clock },
          ].map((atv, i) => (
            <div key={i} className="flex items-center justify-between p-2 rounded bg-secondary/20">
              <div className="flex items-center gap-2">
                <atv.icon className="w-3.5 h-3.5 text-muted-foreground" />
                <span className="text-sm">{atv.texto}</span>
              </div>
              <span className="text-xs text-muted-foreground">{atv.data}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}