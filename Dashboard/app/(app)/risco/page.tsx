// app/gestao-risco/page.tsx
"use client"

import { useState, useEffect } from "react"
import {
  Shield, Calculator, TrendingUp, TrendingDown,
  AlertTriangle, Target, DollarSign, Percent,
  Activity, Zap, Brain, ChevronDown, ChevronUp,
  RotateCcw, Play, Loader2, CheckCircle2, XCircle
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { API_BASE_URL } from "@/lib/api"

// ============================================
// TIPOS
// ============================================

interface MetricasRisco {
  metricas: Record<string, Record<string, { acertos: number; erros: number; total: number; acuracia: number }>>
  melhores_horizontes: Array<{ moeda: string; horizonte: string; acuracia: number; total: number }>
  piores_horizontes: Array<{ moeda: string; horizonte: string; acuracia: number; total: number }>
  acuracia_global: number
  total_trades_global: number
  regime_mercado: string
  recomendacao: string
  cor_regime: string
}

interface SimulacaoResult {
  parametros: {
    capital: number
    risco_percentual: number
    stop_loss: number
    take_profit: number
    risk_reward: number
    acuracia_usada: number
    moeda: string
  }
  resultados: {
    acertos: number
    erros: number
    ganho_total: number
    perda_total: number
    lucro_liquido: number
    capital_final: number
    roi: number
    max_drawdown: number
    drawdown_percentual: number
  }
  qualidade: string
  qualidade_cor: string
}

// ============================================
// COMPONENTE
// ============================================

export default function GestaoRiscoPage() {
  const [metricas, setMetricas] = useState<MetricasRisco | null>(null)
  const [loading, setLoading] = useState(true)
  
  // Simulador
  const [capital, setCapital] = useState(10000)
  const [risco, setRisco] = useState(2)
  const [stopLoss, setStopLoss] = useState(-5)
  const [takeProfit, setTakeProfit] = useState(10)
  const [acuracia, setAcuracia] = useState(66)
  const [numTrades, setNumTrades] = useState(100)
  const [moedaSim, setMoedaSim] = useState("BTC")
  const [simulacao, setSimulacao] = useState<SimulacaoResult | null>(null)
  const [simulando, setSimulando] = useState(false)

  useEffect(() => {
    fetchMetricas()
  }, [])

  async function fetchMetricas() {
    try {
      const res = await fetch(`${API_BASE_URL}/gestao-risco/metricas`)
      const json = await res.json()
      setMetricas(json)
    } catch (e) {
      console.error("Erro ao buscar métricas:", e)
    } finally {
      setLoading(false)
    }
  }

  async function simular() {
    setSimulando(true)
    try {
      const res = await fetch(`${API_BASE_URL}/gestao-risco/simular`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          capital,
          risco_percentual: risco,
          stop_loss: stopLoss,
          take_profit: takeProfit,
          acuracia,
          num_trades: numTrades,
          moeda: moedaSim
        })
      })
      const json = await res.json()
      setSimulacao(json)
    } catch (e) {
      console.error("Erro ao simular:", e)
    } finally {
      setSimulando(false)
    }
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
        <h1 className="text-2xl font-bold">Gestão de Risco</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Proteja seu capital com dados reais da IA
        </p>
      </div>

      {/* REGIME DE MERCADO */}
      {metricas && (
        <div className={cn(
          "rounded-xl p-6 border",
          metricas.cor_regime === "green" ? "bg-green-500/10 border-green-500/20" :
          metricas.cor_regime === "cyan" ? "bg-cyan-500/10 border-cyan-500/20" :
          metricas.cor_regime === "yellow" ? "bg-yellow-500/10 border-yellow-500/20" :
          "bg-red-500/10 border-red-500/20"
        )}>
          <div className="flex items-center gap-3 mb-3">
            <AlertTriangle className={cn("w-6 h-6",
              metricas.cor_regime === "green" ? "text-green-400" :
              metricas.cor_regime === "cyan" ? "text-cyan-400" :
              metricas.cor_regime === "yellow" ? "text-yellow-400" :
              "text-red-400"
            )} />
            <div>
              <h2 className="text-lg font-bold">Regime Atual: {metricas.regime_mercado}</h2>
              <p className="text-sm">Acurácia global: {metricas.acuracia_global}% • {metricas.total_trades_global.toLocaleString()} trades</p>
            </div>
          </div>
          <div className={cn(
            "px-4 py-3 rounded-lg",
            metricas.cor_regime === "green" ? "bg-green-500/20 text-green-400" :
            metricas.cor_regime === "cyan" ? "bg-cyan-500/20 text-cyan-400" :
            metricas.cor_regime === "yellow" ? "bg-yellow-500/20 text-yellow-400" :
            "bg-red-500/20 text-red-400"
          )}>
            <strong>Recomendação:</strong> {metricas.recomendacao}
          </div>
        </div>
      )}

      {/* SIMULADOR */}
      <div className="grid grid-cols-2 gap-6">
        {/* Inputs */}
        <div className="rounded-xl border border-border/50 bg-secondary/10 p-6 space-y-4">
          <h3 className="text-lg font-bold flex items-center gap-2">
            <Calculator className="w-5 h-5 text-cyan-400" />
            Simulador de Cenários
          </h3>
          
          <div className="space-y-3">
            {[
              { label: "Capital (R$)", value: capital, set: setCapital, min: 100, max: 1000000, step: 1000, icon: DollarSign },
              { label: "Risco por Trade (%)", value: risco, set: setRisco, min: 0.5, max: 10, step: 0.5, icon: Percent },
              { label: "Stop Loss (%)", value: stopLoss, set: setStopLoss, min: -20, max: -1, step: 1, icon: TrendingDown },
              { label: "Take Profit (%)", value: takeProfit, set: setTakeProfit, min: 1, max: 50, step: 1, icon: TrendingUp },
            ].map((input, i) => (
              <div key={i}>
                <label className="text-xs text-muted-foreground flex items-center gap-1 mb-1">
                  <input.icon className="w-3 h-3" />
                  {input.label}: <strong>{input.value}{input.label.includes("%") ? "%" : ""}</strong>
                </label>
                <input
                  type="range"
                  value={input.value}
                  onChange={e => input.set(Number(e.target.value))}
                  min={input.min}
                  max={input.max}
                  step={input.step}
                  className="w-full h-2 rounded-full bg-secondary/50 appearance-none cursor-pointer accent-cyan-400"
                />
              </div>
            ))}
            
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">
                <Brain className="w-3 h-3 inline mr-1" />
                Moeda: 
                <select value={moedaSim} onChange={e => setMoedaSim(e.target.value)} className="bg-secondary/30 rounded ml-1 px-2 py-0.5 text-xs">
                  <option>BTC</option>
                  <option>ETH</option>
                  <option>BNB</option>
                </select>
              </label>
            </div>
            
            <div>
              <label className="text-xs text-muted-foreground flex items-center gap-1 mb-1">
                <Target className="w-3 h-3" />
                Acurácia: <strong>{acuracia}%</strong> | Nº Trades: <strong>{numTrades}</strong>
              </label>
              <div className="flex gap-2">
                <input type="range" value={acuracia} onChange={e => setAcuracia(Number(e.target.value))} min={40} max={80} step={1} className="flex-1 h-2 rounded-full bg-secondary/50 accent-green-400" />
                <input type="range" value={numTrades} onChange={e => setNumTrades(Number(e.target.value))} min={10} max={1000} step={10} className="flex-1 h-2 rounded-full bg-secondary/50 accent-purple-400" />
              </div>
            </div>
          </div>

          <Button onClick={simular} disabled={simulando} className="w-full bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500">
            {simulando ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Play className="w-4 h-4 mr-2" />}
            SIMULAR {numTrades} TRADES
          </Button>
        </div>

        {/* Resultados */}
        <div className="rounded-xl border border-border/50 bg-secondary/10 p-6">
          <h3 className="text-lg font-bold flex items-center gap-2 mb-4">
            <Activity className="w-5 h-5 text-green-400" />
            Resultado da Simulação
          </h3>
          
          {simulacao ? (
            <div className="space-y-4">
              <div className={cn(
                "rounded-xl p-4 text-center",
                simulacao.qualidade_cor === "green" ? "bg-green-500/10 border border-green-500/20" :
                simulacao.qualidade_cor === "cyan" ? "bg-cyan-500/10 border border-cyan-500/20" :
                simulacao.qualidade_cor === "yellow" ? "bg-yellow-500/10 border border-yellow-500/20" :
                "bg-red-500/10 border border-red-500/20"
              )}>
                <p className={cn("text-2xl font-bold",
                  simulacao.qualidade_cor === "green" ? "text-green-400" :
                  simulacao.qualidade_cor === "cyan" ? "text-cyan-400" :
                  simulacao.qualidade_cor === "yellow" ? "text-yellow-400" :
                  "text-red-400"
                )}>
                  {simulacao.qualidade}
                </p>
                <p className="text-xs text-muted-foreground mt-1">Qualidade da Estratégia</p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                {[
                  { label: "Capital Final", value: `R$ ${simulacao.resultados.capital_final.toLocaleString()}`, color: simulacao.resultados.lucro_liquido >= 0 ? "text-green-400" : "text-red-400" },
                  { label: "Lucro Líquido", value: `R$ ${simulacao.resultados.lucro_liquido.toLocaleString()}`, color: simulacao.resultados.lucro_liquido >= 0 ? "text-green-400" : "text-red-400" },
                  { label: "ROI", value: `${simulacao.resultados.roi}%`, color: simulacao.resultados.roi >= 0 ? "text-green-400" : "text-red-400" },
                  { label: "Drawdown Máx.", value: `-${simulacao.resultados.drawdown_percentual}%`, color: "text-yellow-400" },
                ].map((card, i) => (
                  <div key={i} className="rounded-lg bg-secondary/20 p-3">
                    <p className="text-[10px] text-muted-foreground">{card.label}</p>
                    <p className={cn("text-lg font-bold", card.color)}>{card.value}</p>
                  </div>
                ))}
              </div>

              <div className="flex items-center gap-4 text-sm">
                <div className="flex items-center gap-1">
                  <CheckCircle2 className="w-4 h-4 text-green-400" />
                  <span className="text-green-400">{simulacao.resultados.acertos} acertos</span>
                </div>
                <div className="flex items-center gap-1">
                  <XCircle className="w-4 h-4 text-red-400" />
                  <span className="text-red-400">{simulacao.resultados.erros} erros</span>
                </div>
                <div className="text-xs text-muted-foreground">
                  R/R: 1:{simulacao.parametros.risk_reward}
                </div>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-48 text-muted-foreground">
              <p>Clique em SIMULAR para ver os resultados</p>
            </div>
          )}
        </div>
      </div>

      {/* MELHORES E PIORES HORIZONTES */}
      {metricas && (
        <div className="grid grid-cols-2 gap-6">
          <div className="rounded-xl border border-border/50 bg-secondary/10 p-4">
            <h3 className="text-sm font-bold text-green-400 mb-3">🟢 Melhores Horizontes</h3>
            <div className="space-y-2">
              {metricas.melhores_horizontes.map((h, i) => (
                <div key={i} className="flex justify-between text-xs">
                  <span>{h.moeda} • {h.horizonte}</span>
                  <span className="text-green-400 font-bold">{h.acuracia}%</span>
                </div>
              ))}
            </div>
          </div>
          <div className="rounded-xl border border-border/50 bg-secondary/10 p-4">
            <h3 className="text-sm font-bold text-red-400 mb-3">🔴 Piores Horizontes</h3>
            <div className="space-y-2">
              {metricas.piores_horizontes.map((h, i) => (
                <div key={i} className="flex justify-between text-xs">
                  <span>{h.moeda} • {h.horizonte}</span>
                  <span className="text-red-400 font-bold">{h.acuracia}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}