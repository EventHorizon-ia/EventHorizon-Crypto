// app/historico/page.tsx
"use client"

import { useState, useEffect } from "react"
import {
  Clock, TrendingUp, TrendingDown, CheckCircle2,
  XCircle, Target, BarChart3, Filter, Calendar,
  Download, Search, ChevronDown, Zap
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { API_BASE_URL } from "@/lib/api"

// ============================================
// TIPOS
// ============================================

interface Trade {
  moeda: string
  horizonte: string
  horizonte_s: number
  acertos: number
  erros: number
  total: number
  acuracia: number
  confianca: number
  preco_atual: number
  timestamp: number
  status: string
}

interface HistoricoData {
  trades: Trade[]
  resumo: {
    total_trades: number
    total_acertos: number
    total_erros: number
    acuracia_geral: number
    total_moedas: number
    horizontes_ativos: number
  }
}

// ============================================
// COMPONENTE
// ============================================

export default function HistoricoPage() {
  const [data, setData] = useState<HistoricoData | null>(null)
  const [loading, setLoading] = useState(true)
  const [filtroMoeda, setFiltroMoeda] = useState("TODAS")
  const [filtroHorizonte, setFiltroHorizonte] = useState("TODOS")
  const [ordenacao, setOrdenacao] = useState<"acuracia" | "total" | "recente">("acuracia")

  // Fetch
  useEffect(() => {
    fetchHistorico()
    const interval = setInterval(fetchHistorico, 10000) // Atualiza a cada 10s
    return () => clearInterval(interval)
  }, [])

  async function fetchHistorico() {
    try {
      const res = await fetch(`${API_BASE_URL}/historico`)
      const json = await res.json()
      setData(json)
    } catch (e) {
      console.error("Erro ao buscar histórico:", e)
    } finally {
      setLoading(false)
    }
  }

  // Filtros
  const moedasUnicas = data ? [...new Set(data.trades.map(t => t.moeda))] : []
  const horizontesUnicos = data ? [...new Set(data.trades.map(t => t.horizonte))] : []

  const tradesFiltrados = data?.trades
    .filter(t => filtroMoeda === "TODAS" || t.moeda === filtroMoeda)
    .filter(t => filtroHorizonte === "TODOS" || t.horizonte === filtroHorizonte)
    .sort((a, b) => {
      if (ordenacao === "acuracia") return b.acuracia - a.acuracia
      if (ordenacao === "total") return b.total - a.total
      return b.timestamp - a.timestamp
    }) || []

  // Cores por acurácia
  function getAcuraciaColor(valor: number) {
    if (valor >= 60) return "text-green-400"
    if (valor >= 50) return "text-yellow-400"
    return "text-red-400"
  }

  function getAcuraciaBg(valor: number) {
    if (valor >= 60) return "bg-green-500/10 border-green-500/20"
    if (valor >= 50) return "bg-yellow-500/10 border-yellow-500/20"
    return "bg-red-500/10 border-red-500/20"
  }

  // Loading
  if (loading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-4rem)]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400 mx-auto mb-3" />
          <p className="text-sm text-muted-foreground">Carregando histórico...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Histórico de Trades</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Resultados verificados com preços reais após cada horizonte
          </p>
        </div>
        <Button className="bg-secondary/50 border border-border/50 hover:bg-secondary/70 text-xs">
          <Download className="w-3.5 h-3.5 mr-2" />
          Exportar CSV
        </Button>
      </div>

      {/* Cards de Resumo */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: "Total de Trades", value: data?.resumo.total_trades.toLocaleString() || "0", icon: BarChart3, color: "text-cyan-400", bg: "bg-cyan-500/10 border-cyan-500/20" },
          { label: "Acertos", value: data?.resumo.total_acertos.toLocaleString() || "0", icon: CheckCircle2, color: "text-green-400", bg: "bg-green-500/10 border-green-500/20" },
          { label: "Erros", value: data?.resumo.total_erros.toLocaleString() || "0", icon: XCircle, color: "text-red-400", bg: "bg-red-500/10 border-red-500/20" },
          { label: "Acurácia Geral", value: `${data?.resumo.acuracia_geral || 0}%`, icon: Target, color: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/20" },
        ].map((card, i) => (
          <div key={i} className={cn("rounded-xl p-4 border", card.bg)}>
            <div className="flex items-center gap-2 mb-2">
              <card.icon className={cn("w-4 h-4", card.color)} />
              <span className="text-xs text-muted-foreground">{card.label}</span>
            </div>
            <p className={cn("text-2xl font-bold", card.color)}>{card.value}</p>
          </div>
        ))}
      </div>

      {/* Filtros */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-secondary/30 border border-border/50">
          <Filter className="w-3.5 h-3.5 text-muted-foreground" />
          <select
            value={filtroMoeda}
            onChange={e => setFiltroMoeda(e.target.value)}
            className="bg-transparent text-xs text-muted-foreground outline-none"
          >
            <option value="TODAS">Todas as moedas ({data?.resumo.total_moedas || 0})</option>
            {moedasUnicas.map(m => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-secondary/30 border border-border/50">
          <Clock className="w-3.5 h-3.5 text-muted-foreground" />
          <select
            value={filtroHorizonte}
            onChange={e => setFiltroHorizonte(e.target.value)}
            className="bg-transparent text-xs text-muted-foreground outline-none"
          >
            <option value="TODOS">Todos os horizontes</option>
            {horizontesUnicos.map(h => (
              <option key={h} value={h}>{h}</option>
            ))}
          </select>
        </div>

        <div className="flex gap-1 ml-auto">
          {(["acuracia", "total", "recente"] as const).map(ord => (
            <button
              key={ord}
              onClick={() => setOrdenacao(ord)}
              className={cn(
                "px-3 py-1.5 rounded-lg text-xs",
                ordenacao === ord
                  ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30"
                  : "bg-secondary/30 text-muted-foreground border border-border/50"
              )}
            >
              {{ acuracia: "Acurácia", total: "Volume", recente: "Recente" }[ord]}
            </button>
          ))}
        </div>
      </div>

      {/* Tabela de Trades */}
      <div className="rounded-xl border border-border/50 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-secondary/20 border-b border-border/50 text-muted-foreground">
                <th className="text-left p-3 font-medium">Moeda</th>
                <th className="text-left p-3 font-medium">Horizonte</th>
                <th className="text-right p-3 font-medium">Acertos</th>
                <th className="text-right p-3 font-medium">Erros</th>
                <th className="text-right p-3 font-medium">Total</th>
                <th className="text-right p-3 font-medium">Acurácia</th>
                <th className="text-right p-3 font-medium">Confiança</th>
                <th className="text-center p-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {tradesFiltrados.length > 0 ? (
                tradesFiltrados.map((trade, idx) => (
                  <tr key={idx} className="border-b border-border/20 hover:bg-secondary/10 transition-colors">
                    <td className="p-3">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-foreground">{trade.moeda}</span>
                        <span className="text-xs text-muted-foreground">${trade.preco_atual?.toLocaleString()}</span>
                      </div>
                    </td>
                    <td className="p-3">
                      <span className="px-2 py-0.5 rounded bg-secondary/30 text-xs font-mono">
                        {trade.horizonte}
                      </span>
                    </td>
                    <td className="p-3 text-right text-green-400 font-medium">{trade.acertos}</td>
                    <td className="p-3 text-right text-red-400 font-medium">{trade.erros}</td>
                    <td className="p-3 text-right font-medium">{trade.total}</td>
                    <td className="p-3 text-right">
                      <span className={cn("font-bold font-mono", getAcuraciaColor(trade.acuracia))}>
                        {trade.acuracia}%
                      </span>
                    </td>
                    <td className="p-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <div className="w-16 h-1.5 rounded-full bg-secondary/50 overflow-hidden">
                          <div
                            className={cn("h-full rounded-full", trade.confianca >= 60 ? "bg-green-400" : trade.confianca >= 50 ? "bg-yellow-400" : "bg-red-400")}
                            style={{ width: `${trade.confianca}%` }}
                          />
                        </div>
                        <span className="text-xs text-muted-foreground">{trade.confianca}%</span>
                      </div>
                    </td>
                    <td className="p-3 text-center">
                      <span className={cn(
                        "px-2 py-0.5 rounded-full text-[10px] font-medium border",
                        trade.acuracia >= 60
                          ? "bg-green-500/10 text-green-400 border-green-500/20"
                          : trade.acuracia >= 50
                          ? "bg-yellow-500/10 text-yellow-400 border-yellow-500/20"
                          : "bg-red-500/10 text-red-400 border-red-500/20"
                      )}>
                        {trade.acuracia >= 60 ? "RECOMENDADO" : trade.acuracia >= 50 ? "APRENDENDO" : "EVITAR"}
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={8} className="p-8 text-center text-muted-foreground">
                    <Zap className="w-8 h-8 mx-auto mb-2 opacity-30" />
                    <p className="text-sm">Nenhum trade encontrado</p>
                    <p className="text-xs mt-1">Os dados aparecerão conforme a IA gera e verifica previsões.</p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Footer info */}
      <div className="text-center text-[10px] text-muted-foreground">
        {data?.resumo.total_moedas || 0} moedas • {data?.resumo.horizontes_ativos || 0} horizontes • Dados verificados com preços reais da Binance
      </div>
    </div>
  )
}