// app/performance/page.tsx
"use client"

import { useState, useEffect } from "react"
import {
  TrendingUp, TrendingDown, Brain, Target,
  Activity, Zap, BarChart3, LineChart,
  ArrowUp, ArrowDown, Minus, Sparkles,
  Loader2
} from "lucide-react"
import { cn } from "@/lib/utils"
import { API_BASE_URL } from "@/lib/api"

// ============================================
// TIPOS
// ============================================

interface MenteMetrica {
  moeda: string
  geracao: number
  acuracia_media: number
  acuracia_micro: number
  acuracia_intraday: number
  acuracia_swing: number
  acuracia_position: number
  loss_medio: number
  confianca: number
  estabilidade: string
  tendencia: string
  acuracias_reais: Record<string, { acertos: number; erros: number; total: number; acuracia: number }>
  accuracy_por_horizonte: number[]
}

interface PerformanceData {
  mentes: MenteMetrica[]
  resumo: {
    total_moedas: number
    total_geracoes: number
    acuracia_media_geral: number
    moeda_top: string
    estabilidade_geral: string
  }
}

// ============================================
// COMPONENTE
// ============================================

export default function PerformancePage() {
  const [data, setData] = useState<PerformanceData | null>(null)
  const [selectedMoeda, setSelectedMoeda] = useState<string>("BTC")
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchMetricas()
    const interval = setInterval(fetchMetricas, 5000)
    return () => clearInterval(interval)
  }, [])

  async function fetchMetricas() {
    try {
      const res = await fetch(`${API_BASE_URL}/performance/metricas`)
      const json = await res.json()
      setData(json)
      if (!selectedMoeda && json.mentes?.length > 0) {
        setSelectedMoeda(json.mentes[0].moeda)
      }
    } catch (e) {
      console.error("Erro ao buscar métricas:", e)
    } finally {
      setLoading(false)
    }
  }

  const selectedMente = data?.mentes?.find(m => m.moeda === selectedMoeda)

  // Cores
  function getTendenciaColor(tendencia: string) {
    if (tendencia === "melhorando") return "text-green-400"
    if (tendencia === "piorando") return "text-red-400"
    return "text-yellow-400"
  }

  function getTendenciaIcon(tendencia: string) {
    if (tendencia === "melhorando") return ArrowUp
    if (tendencia === "piorando") return ArrowDown
    return Minus
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-4rem)]">
        <Loader2 className="w-8 h-8 animate-spin text-cyan-400" />
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Performance da IA</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Métricas de aprendizado em tempo real • {data?.resumo.total_geracoes.toLocaleString()} gerações totais
        </p>
      </div>

      {/* Cards de Resumo */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: "Acurácia Média", value: `${data?.resumo.acuracia_media_geral || 0}%`, icon: Target, color: "text-green-400", bg: "bg-green-500/10 border-green-500/20" },
          { label: "Total de Gerações", value: data?.resumo.total_geracoes?.toLocaleString() || "0", icon: Zap, color: "text-cyan-400", bg: "bg-cyan-500/10 border-cyan-500/20" },
          { label: "Moedas Ativas", value: data?.resumo.total_moedas || 0, icon: Brain, color: "text-purple-400", bg: "bg-purple-500/10 border-purple-500/20" },
          { label: "Estabilidade", value: data?.resumo.estabilidade_geral === "estável" ? "ESTÁVEL" : "MODERADA", icon: Activity, color: data?.resumo.estabilidade_geral === "estável" ? "text-green-400" : "text-yellow-400", bg: data?.resumo.estabilidade_geral === "estável" ? "bg-green-500/10 border-green-500/20" : "bg-yellow-500/10 border-yellow-500/20" },
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

      {/* Seletor de Moeda */}
      <div className="flex gap-2">
        {data?.mentes?.map(m => (
          <button
            key={m.moeda}
            onClick={() => setSelectedMoeda(m.moeda)}
            className={cn(
              "px-4 py-2 rounded-lg text-sm font-medium transition-all",
              selectedMoeda === m.moeda
                ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30"
                : "bg-secondary/30 text-muted-foreground border border-border/50 hover:bg-secondary/50"
            )}
          >
            {m.moeda}
          </button>
        ))}
      </div>

      {/* Detalhes da Mente Selecionada */}
      {selectedMente && (
        <>
          {/* Cards da Mente */}
          <div className="grid grid-cols-4 gap-3">
            {[
              { label: "Geração Atual", value: selectedMente.geracao.toLocaleString(), color: "text-white" },
              { label: "Acurácia Média", value: selectedMente.acuracia_media, color: "text-green-400" },
              { label: "Loss Médio", value: selectedMente.loss_medio.toFixed(4), color: "text-yellow-400" },
              { label: "Confiança", value: selectedMente.confianca, color: "text-cyan-400" },
            ].map((card, i) => (
              <div key={i} className="rounded-xl p-4 bg-secondary/20 border border-border/50">
                <p className="text-xs text-muted-foreground mb-1">{card.label}</p>
                <p className={cn("text-xl font-bold", card.color)}>{card.value}</p>
              </div>
            ))}
          </div>

          {/* Tendência */}
          <div className="rounded-xl p-4 bg-secondary/10 border border-border/50">
            <div className="flex items-center gap-2 mb-3">
              {(() => {
                const Icon = getTendenciaIcon(selectedMente.tendencia)
                return <Icon className={cn("w-5 h-5", getTendenciaColor(selectedMente.tendencia))} />
              })()}
              <span className="text-sm font-medium">
                Tendência: <span className={getTendenciaColor(selectedMente.tendencia)}>{selectedMente.tendencia.toUpperCase()}</span>
              </span>
            </div>
          </div>

          {/* GRÁFICO DE BARRAS - Acurácia por Horizonte */}
          <div className="rounded-xl p-4 bg-secondary/10 border border-border/50">
            <h3 className="text-sm font-bold mb-4">Acurácia por Horizonte (verificada)</h3>
            <div className="space-y-3">
              {[
                { label: "5 segundos", h: "5", cor: "bg-blue-400" },
                { label: "15 segundos", h: "15", cor: "bg-cyan-400" },
                { label: "30 segundos", h: "30", cor: "bg-teal-400" },
                { label: "1 minuto", h: "60", cor: "bg-green-400" },
                { label: "5 minutos", h: "300", cor: "bg-lime-400" },
                { label: "15 minutos", h: "900", cor: "bg-yellow-400" },
                { label: "30 minutos", h: "1800", cor: "bg-orange-400" },
                { label: "1 hora", h: "3600", cor: "bg-red-400" },
              ].map(item => {
                const acc = selectedMente.acuracias_reais?.[item.h]
                const valor = acc?.acuracia || 0
                const total = acc?.total || 0
                const mostrar = total > 10
                
                return (
                  <div key={item.h} className="flex items-center gap-3">
                    <span className="text-xs text-muted-foreground w-24 text-right">{item.label}</span>
                    <div className="flex-1 h-6 bg-secondary/30 rounded-full overflow-hidden">
                      <div
                        className={cn("h-full rounded-full transition-all duration-500 flex items-center justify-end px-2", item.cor)}
                        style={{ width: `${mostrar ? valor : 0}%`, opacity: mostrar ? 1 : 0.3 }}
                      >
                        {mostrar && (
                          <span className="text-[10px] font-bold text-white drop-shadow">
                            {valor}%
                          </span>
                        )}
                      </div>
                    </div>
                    <span className="text-[10px] text-muted-foreground w-16">
                      {mostrar ? `${total} trades` : "poucos dados"}
                    </span>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Acurácia por Tipo de Horizonte */}
          <div className="grid grid-cols-4 gap-3">
            {[
              { label: "Micro", value: selectedMente.acuracia_micro, desc: "5s - 1min", color: "text-blue-400", bg: "bg-blue-500/10 border-blue-500/20" },
              { label: "Intraday", value: selectedMente.acuracia_intraday, desc: "5min - 30min", color: "text-green-400", bg: "bg-green-500/10 border-green-500/20" },
              { label: "Swing", value: selectedMente.acuracia_swing, desc: "1h - 5h", color: "text-orange-400", bg: "bg-orange-500/10 border-orange-500/20" },
              { label: "Position", value: selectedMente.acuracia_position, desc: "1 dia", color: "text-purple-400", bg: "bg-purple-500/10 border-purple-500/20" },
            ].map((card, i) => (
              <div key={i} className={cn("rounded-xl p-4 border", card.bg)}>
                <p className="text-xs text-muted-foreground mb-1">{card.label}</p>
                <p className={cn("text-2xl font-bold", card.color)}>{(card.value).toFixed(1)}%</p>
                <p className="text-[10px] text-muted-foreground mt-1">{card.desc}</p>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}