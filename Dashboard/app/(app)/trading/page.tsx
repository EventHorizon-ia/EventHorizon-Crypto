"use client"

import { useState, useEffect, useCallback } from "react"
import {
  Loader2, TrendingUp, TrendingDown, Activity,
  Radio, ArrowUp, ArrowDown, Zap
} from "lucide-react"
import { cn } from "@/lib/utils"
import { TradingChart } from "@/components/apps/TradingChart"
import { API_BASE_URL } from "@/lib/api"

// ============================================
// TIPOS
// ============================================

interface MoedaRealtime {
  symbol: string
  price: number
  rsi: number
  regime: string
  geracoes: number
  acuracias_reais: Record<string, { acertos: number; erros: number; total: number; acuracia: number }>
  previsoes: Record<string, number>
}

interface RealtimeData {
  moedas: MoedaRealtime[]
  total_moedas: number
  total_verificacoes: number
  melhor_moeda: MoedaRealtime | null
}

// ============================================
// COMPONENTE
// ============================================

export default function TradingPage() {
  const [realtimeData, setRealtimeData] = useState<RealtimeData | null>(null)
  const [selectedSymbol, setSelectedSymbol] = useState("BTC")
  const [candles, setCandles] = useState<any[]>([])
  const [currentPrice, setCurrentPrice] = useState(0)
  const [previsoes, setPrevisoes] = useState<Record<string, number>>({})
  const [isRunning, setIsRunning] = useState(false)

  const fetchRealtimeData = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/dashboard/realtime`)
      const data = await res.json()
      setRealtimeData(data)
      setIsRunning(data.total_moedas > 0)
    } catch {}
  }, [])

  const fetchCandles = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/status`)
      const data = await res.json()
      const cryptoWithSymbol = data.dados?.find(
        (d: any) => d.symbol === `${selectedSymbol}USDT`
      )
      if (cryptoWithSymbol) {
        setCandles(cryptoWithSymbol.candles || [])
        setCurrentPrice(cryptoWithSymbol.price || 0)
        setPrevisoes({
          "5s": cryptoWithSymbol.previsao_5s || 0,
          "15s": cryptoWithSymbol.previsao_15s || 0,
          "30s": cryptoWithSymbol.previsao_30s || 0,
          "60s": cryptoWithSymbol.previsao_60s || 0,
          "5min": cryptoWithSymbol.previsao_300s || 0,
          "15min": cryptoWithSymbol.previsao_900s || 0,
          "30min": cryptoWithSymbol.previsao_1800s || 0,
          "1h": cryptoWithSymbol.previsao_3600s || 0,
          "5h": cryptoWithSymbol.previsao_18000s || 0,
          "1d": cryptoWithSymbol.previsao_86400s || 0,
        })
      }
    } catch {}
  }, [selectedSymbol])

  useEffect(() => {
    fetchRealtimeData()
    fetchCandles()
    const realtimeInterval = setInterval(fetchRealtimeData, 3000)
    const candlesInterval = setInterval(fetchCandles, 5000)
    return () => {
      clearInterval(realtimeInterval)
      clearInterval(candlesInterval)
    }
  }, [fetchRealtimeData, fetchCandles])

  const totalPrevisoes = realtimeData?.total_verificacoes || 0

  const acuraciaGeral = (() => {
    if (!realtimeData?.moedas?.length) return 0
    const todasAcuracias = realtimeData.moedas
      .flatMap(m => Object.values(m.acuracias_reais))
      .filter(a => a.total > 10)
    if (todasAcuracias.length === 0) return 0
    const soma = todasAcuracias.reduce((acc, a) => acc + a.acuracia, 0)
    return Math.round(soma / todasAcuracias.length)
  })()

  const sinaisOrdenados = (realtimeData?.moedas || [])
    .map(moeda => {
      const previsao15min = moeda.previsoes?.["15min"] || 0
      const acuracia15min = moeda.acuracias_reais?.["900"]
      return {
        symbol: moeda.symbol,
        previsao: previsao15min,
        confianca: acuracia15min?.acuracia || 50,
        total: acuracia15min?.total || 0,
      }
    })
    .filter(s => Math.abs(s.previsao) > 0.01)
    .sort((a, b) => Math.abs(b.previsao) - Math.abs(a.previsao))

  const selectedData = realtimeData?.moedas?.find(m => m.symbol === selectedSymbol)

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border/50 bg-secondary/10">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600">
            <Radio className="w-4 h-4 text-white" />
          </div>
          <div>
            <h1 className="text-base font-bold">Trading Ao Vivo</h1>
            <p className="text-[10px] text-muted-foreground">
              {totalPrevisoes.toLocaleString()} verificações • {acuraciaGeral}% acurácia geral
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {isRunning ? (
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-green-500/20 text-green-400 border border-green-500/30">
              <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" /> AO VIVO
            </span>
          ) : (
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-gray-500/20 text-gray-400 border border-gray-500/30">
              <div className="w-2 h-2 rounded-full bg-gray-400" /> PARADO
            </span>
          )}
        </div>
      </div>

      {/* Área do gráfico */}
      <div className="flex-1 p-3 overflow-y-auto space-y-3">
        {/* Cards de top moedas */}
        <div className="grid grid-cols-4 gap-2">
          {(realtimeData?.moedas || []).slice(0, 4).map(coin => {
            const isSelected = coin.symbol === selectedSymbol
            const previsao15min = coin.previsoes?.["15min"] || 0
            return (
              <button
                key={coin.symbol}
                onClick={() => setSelectedSymbol(coin.symbol)}
                className={cn(
                  "p-3 rounded-xl border text-left transition-all",
                  isSelected ? "border-cyan-500/50 bg-cyan-500/10" : "border-border/50 bg-secondary/20 hover:bg-secondary/30"
                )}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-bold">{coin.symbol}</span>
                  {previsao15min > 0 ? <ArrowUp className="w-3 h-3 text-green-400" /> : <ArrowDown className="w-3 h-3 text-red-400" />}
                </div>
                <p className="text-lg font-bold">${coin.price?.toLocaleString(undefined, { maximumFractionDigits: 2 })}</p>
                <div className="flex items-center gap-1 mt-1">
                  <span className={cn("text-[10px]", previsao15min >= 0 ? "text-green-400" : "text-red-400")}>
                    {previsao15min > 0 ? "+" : ""}{previsao15min.toFixed(2)}%
                  </span>
                  <span className="text-[10px] text-muted-foreground">15min</span>
                </div>
              </button>
            )
          })}
        </div>

        {/* Gráfico principal */}
        <div className="rounded-xl border border-border/50 bg-secondary/10 p-2">
          {candles.length > 0 ? (
            <TradingChart
              candles={candles}
              currentPrice={currentPrice}
              prediction={previsoes["5s"] || 0}
              symbol={`${selectedSymbol}USDT`}
              isActive={isRunning}
              timeframe={5}
              chartType="candlestick"
              showIndicators={true}
              prediction5s={previsoes["5s"]}
              prediction15s={previsoes["15s"]}
              prediction30s={previsoes["30s"]}
              prediction60s={previsoes["60s"]}
              prediction300s={previsoes["5min"]}
              prediction900s={previsoes["15min"]}
              prediction1800s={previsoes["30min"]}
              prediction3600s={previsoes["1h"]}
              prediction18000s={previsoes["5h"]}
              prediction86400s={previsoes["1d"]}
            />
          ) : (
            <div className="h-80 flex items-center justify-center text-muted-foreground text-sm">
              <Loader2 className="w-5 h-5 animate-spin mr-2" /> Carregando gráfico...
            </div>
          )}
        </div>

        {/* Previsões 10 horizontes */}
        {selectedData && (
          <div className="rounded-xl border border-border/50 bg-secondary/10 p-3">
            <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-2">Previsões — {selectedSymbol}</p>
            <div className="grid grid-cols-5 gap-1.5">
              {[
                { time: "5s", value: previsoes["5s"] || 0 },
                { time: "15s", value: previsoes["15s"] || 0 },
                { time: "30s", value: previsoes["30s"] || 0 },
                { time: "60s", value: previsoes["60s"] || 0 },
                { time: "5min", value: previsoes["5min"] || 0 },
                { time: "15min", value: previsoes["15min"] || 0 },
                { time: "30min", value: previsoes["30min"] || 0 },
                { time: "1h", value: previsoes["1h"] || 0 },
                { time: "5h", value: previsoes["5h"] || 0 },
                { time: "1d", value: previsoes["1d"] || 0 },
              ].map((pred, i) => {
                const isPositive = pred.value >= 0
                const precoAlvo = currentPrice * (1 + pred.value / 100)
                return (
                  <div key={i} className={cn("rounded-lg p-2 text-center border", isPositive ? "border-green-500/20 bg-green-500/5" : "border-red-500/20 bg-red-500/5")}>
                    <div className="text-[10px] text-muted-foreground">{pred.time}</div>
                    <div className={cn("text-xs font-bold font-mono", isPositive ? "text-green-400" : "text-red-400")}>
                      {pred.value > 0 ? "+" : ""}{pred.value.toFixed(2)}%
                    </div>
                    <div className="text-[9px] text-muted-foreground">${precoAlvo.toLocaleString(undefined, { maximumFractionDigits: 2 })}</div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Tabela de Sinais — TODOS os horizontes */}
        <div className="rounded-xl border border-border/50 bg-secondary/10 p-3">
          <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-3">
            Sinais por Horizonte — {selectedSymbol}
          </p>
          
          {realtimeData?.moedas ? (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-muted-foreground border-b border-border/30">
                    <th className="text-left p-2 font-medium">Moeda</th>
                    <th className="text-right p-2">5s</th>
                    <th className="text-right p-2">15s</th>
                    <th className="text-right p-2">30s</th>
                    <th className="text-right p-2">60s</th>
                    <th className="text-right p-2">5min</th>
                    <th className="text-right p-2">15min</th>
                    <th className="text-right p-2">30min</th>
                    <th className="text-right p-2">1h</th>
                    <th className="text-right p-2">Confiança</th>
                  </tr>
                </thead>
                <tbody>
                  {realtimeData.moedas.map(moeda => {
                    // Pega a melhor acurácia como confiança
                    const acuracias = Object.values(moeda.acuracias_reais || {})
                    const melhorConfianca = acuracias.length > 0 
                      ? Math.max(...acuracias.map((a: any) => a.acuracia || 0))
                      : 50
                    
                    return (
                      <tr key={moeda.symbol} className="border-b border-border/20 hover:bg-secondary/20">
                        <td className="p-2 font-medium">{moeda.symbol}</td>
                        {["5s", "15s", "30s", "60s", "5min", "15min", "30min", "1h"].map(h => {
                          const val = moeda.previsoes?.[h] || 0
                          const isPositive = val >= 0
                          return (
                            <td key={h} className={cn(
                              "p-2 text-right font-mono text-xs",
                              isPositive ? "text-green-400" : "text-red-400"
                            )}>
                              {val > 0 ? "+" : ""}{val.toFixed(2)}%
                            </td>
                          )
                        })}
                        <td className="p-2 text-right">
                          <span className={cn(
                            "px-1.5 py-0.5 rounded text-[10px] font-medium",
                            melhorConfianca >= 60 ? "bg-green-500/10 text-green-400" :
                            melhorConfianca >= 50 ? "bg-yellow-500/10 text-yellow-400" :
                            "bg-red-500/10 text-red-400"
                          )}>
                            {melhorConfianca}%
                          </span>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <Activity className="w-8 h-8 mx-auto mb-2 opacity-30" />
              <p className="text-sm">Nenhuma moeda carregada</p>
              <p className="text-xs mt-1">Carregue moedas na aba Crypto Trading.</p>
            </div>
          )}

        </div>
      </div>
    </div>
  )
}