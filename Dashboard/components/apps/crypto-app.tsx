"use client"

import { useState, useEffect, useRef } from "react"
import { 
  Play, Square, RefreshCw, Zap, 
  TrendingUp, TrendingDown, Activity, 
  BarChart3, X, Trash2
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { TradingChart } from "@/components/apps/TradingChart"
import { API_BASE_URL } from '@/lib/api';

const API_BASE = API_BASE_URL
// ============================================
// INTERFACES
// ============================================

interface RawCrypto {
  id: string
  energia?: number
  symbol?: string
  price?: number
  delta?: number
  tipo?: string
  candles?: any[]
  previsao?: number
  // ✅ NOVOS HORIZONTES
  previsao_5s?: number
  previsao_15s?: number
  previsao_30s?: number
  previsao_60s?: number
  previsao_300s?: number
  previsao_900s?: number
  previsao_1800s?: number
  previsao_3600s?: number
  previsao_18000s?: number
  previsao_86400s?: number
  // ✅ CONSENSO
  consenso_curto?: number
  consenso_medio?: number
  consenso_longo?: number
}

interface Crypto {
  id: string
  symbol: string
  price: number
  energy: number
  delta: number
  candles: any[]
  previsao: number
  // ✅ NOVOS HORIZONTES
  previsao_5s?: number
  previsao_15s?: number
  previsao_30s?: number
  previsao_60s?: number
  previsao_300s?: number
  previsao_900s?: number
  previsao_1800s?: number
  previsao_3600s?: number
  previsao_18000s?: number
  previsao_86400s?: number
  // ✅ CONSENSO
  consenso_curto?: number
  consenso_medio?: number
  consenso_longo?: number
}

interface CryptoAppProps {
  cryptos: RawCrypto[]
  executeCommand: (command: string) => Promise<string>
  onRefresh?: () => Promise<void>
  pausePolling?: () => void
  resumePolling?: () => void
  clearUnits?: () => void
  onCoinsRemoved?: (symbols: string[]) => void
}

interface ReportCoin {
  symbol: string
  acertos: number
  erros: number
  total: number
  acuracia: number
  confianca: number
  categoria: "recommended" | "learning" | "bad"
  id: number
}

interface DashboardStats {
  acuracia: number
  total_previsoes: number
  acertos: number
  melhores_horarios: Array<{ hora: string; total: number; acuracia: number }>
  performance_moedas: Array<{ symbol: string; total: number; acuracia: number }>
  tendencia: {
    ultima_hora: number
    direcao: "up" | "down" | "stable"
    variacao: number
  }
}

// ============================================
// HELPERS
// ============================================

const STORAGE_KEY = "trader_loaded_coins"

const availableCoins = [
  "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
  "ADAUSDT", "DOGEUSDT", "DOTUSDT", "MATICUSDT", "LTCUSDT"
]

function getSignalAction(previsao: number) {
  const previsaoPercentual = Math.abs(previsao) * 1000
  const sinal = previsao > 0 ? previsaoPercentual : -previsaoPercentual

  if (sinal > 20)  return { text: "COMPRAR", color: "green", level: "strong" }
  if (sinal > 5)   return { text: "COMPRAR", color: "green", level: "moderate" }
  if (sinal < -20) return { text: "VENDER",  color: "red",   level: "strong" }
  if (sinal < -5)  return { text: "VENDER",  color: "red",   level: "moderate" }
  return { text: "AGUARDAR", color: "gray", level: "neutral" }
}

function parseValidCryptos(rawList: RawCrypto[]): Crypto[] {
  return (rawList ?? [])
    .filter(c => c.symbol && c.price !== undefined)
    .map(c => {
      const previsao = c.previsao ?? 0
      return {
        id: c.id,
        symbol: c.symbol!,
        price: c.price!,
        energy: c.energia ?? 0,
        delta: c.delta ?? 0,
        candles: c.candles ?? [],
        previsao,
        previsao_5s: c.previsao_5s ?? previsao,
        previsao_15s: c.previsao_15s ?? previsao,
        previsao_30s: c.previsao_30s ?? previsao,
        previsao_60s: c.previsao_60s ?? previsao,
        previsao_300s: c.previsao_300s ?? previsao,
        previsao_900s: c.previsao_900s ?? previsao,
        previsao_1800s: c.previsao_1800s ?? previsao,
        previsao_3600s: c.previsao_3600s ?? previsao,
        previsao_18000s: c.previsao_18000s ?? previsao,
        previsao_86400s: c.previsao_86400s ?? previsao,
        consenso_curto: c.consenso_curto ?? 0,
        consenso_medio: c.consenso_medio ?? 0,
        consenso_longo: c.consenso_longo ?? 0,
      }
    })
}

// ============================================
// COMPONENT
// ============================================

export function CryptoApp({ 
  cryptos, 
  executeCommand, 
  onRefresh, 
  pausePolling, 
  resumePolling, 
  clearUnits,
  onCoinsRemoved,
}: CryptoAppProps) {

  // ── UI state ──────────────────────────────
  const [timeframe, setTimeframe] = useState(() => {
    try {
      const config = JSON.parse(localStorage.getItem("trader_config") || "{}")
      return config.timeframePadrao || 5
    } catch {
      return 5
    }
  })

  const [loading,             setLoading]             = useState<string | null>(null)
  const [isRunning,           setIsRunning]           = useState(false)
  const [chartType, setChartType] = useState<"candlestick" | "line" | "area">(() => {
    try {
      const config = JSON.parse(localStorage.getItem("trader_config") || "{}")
      return config.graficoTipo || "candlestick"
    } catch {
      return "candlestick"
    }
  })

  const [showIndicators,      setShowIndicators]      = useState(true)
  const [selectedCoinForChart, setSelectedCoinForChart] = useState(() => {
    try {
      const config = JSON.parse(localStorage.getItem("trader_config") || "{}")
      return config.moedaPadrao || "BTCUSDT"
    } catch {
      return "BTCUSDT"
    }
  })
  
  const [selectedCoins       , setSelectedCoins]      = useState<string[]>([])  // ⭐ Começa vazio
  const [showCoinSelector,    setShowCoinSelector]    = useState(false)
  const [chartKey,            setChartKey]            = useState(0)
  const [notification,        setNotification]        = useState<{ message: string; type: "success" | "error" | "info" } | null>(null)

  // ── Report modal ──────────────────────────
  const [showReportModal,       setShowReportModal]       = useState(false)
  const [reportData,            setReportData]            = useState<ReportCoin[]>([])
  const [selectedCoinsToRemove, setSelectedCoinsToRemove] = useState<string[]>([])
  const [isLoadingReport,       setIsLoadingReport]       = useState(false)

  // ── Clear coins modal ─────────────────────
  const [showClearCoinsModal, setShowClearCoinsModal] = useState(false)
  const [coinsToClear,        setCoinsToClear]        = useState<string[]>([])

  // ── Accuracy cache ────────────────────────
  const [accuracyCache, setAccuracyCache] = useState<Record<string, { acuracia: number; acertos: number; total: number }>>({})

  // ── Dashboard stats ───────────────────────
  const [dashboardStats, setDashboardStats] = useState<DashboardStats>({
    acuracia: 0,
    total_previsoes: 0,
    acertos: 0,
    melhores_horarios: [],
    performance_moedas: [],
    tendencia: { ultima_hora: 0, direcao: "stable", variacao: 0 },
  })

  // ⭐ Dados em tempo real (mesmo endpoint do Dashboard)
  const [realtimeData, setRealtimeData] = useState<any>(null)

  useEffect(() => {
    const fetchRealtime = async () => {
      try {
        const res = await fetch(`${API_BASE}/dashboard/realtime`)
        const json = await res.json()
        setRealtimeData(json)
      } catch (e) {
        // Silencioso - usa fallback dos cryptos
      }
    }
    fetchRealtime()
    const interval = setInterval(fetchRealtime, 3000)
    return () => clearInterval(interval)
  }, [])

    // Junto com os outros useState:
  const [signalResponse, setSignalResponse] = useState<string | null>(null)
  const [signalLoading, setSignalLoading] = useState(false)

  // Função que chama a IA para análise
  

// ⭐ Função que chama o chatbot do backend
async function handleSignalCommand() {
  if (!selected) return
  
  setSignalLoading(true)
  setSignalResponse(null)
  
  try {
    const response = await fetch(`${API_BASE_URL}/chatbot`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ 
        pergunta: `ANÁLISE DE SINAL - ${selected.symbol.replace("USDT", "")}

Dê uma recomendação DIRETA e ACIONÁVEL. O trader quer saber O QUE FAZER.

Formato OBRIGATÓRIO da resposta:

📊 **SINAL: [COMPRAR/VENDER/AGUARDAR]**
💰 Preço atual: $[VALOR]
🎯 Preço alvo: $[VALOR] ([X]%)
🛑 Stop Loss: $[VALOR] ([X]%)
⏱️ Horizonte recomendado: [5min/15min/30min/1h]
📈 Confiança: [X]%

📝 **Análise (máximo 3 frases):**
[Seu raciocínio mais importante]

⚠️ **Risco:** [1 frase sobre o risco]

NÃO FALE de:
- Consenso entre prazos
- RSI (a menos que seja extremo)
- "Mercado em ranging"
- "Mercado lateral"
- Previsões de todos os horizontes (só o horizonte recomendado)

Seja DIRETO. O trader quer AÇÃO.`,
        moeda: selected.symbol,
      })
    })
    const data = await response.json()
    setSignalResponse(data.resposta || "Não foi possível gerar análise.")
  } catch (error) {
    console.error("Erro no chatbot:", error)
    setSignalResponse("❌ Erro ao conectar com o assistente.")
  } finally {
    setSignalLoading(false)
  }
}

  // ============================================
  // DERIVED DATA
  // ── A prop `cryptos` já chega filtrada pelo pai (page.tsx).
  // ── Não há blacklist local. Apenas processar e exibir.
  // ============================================

  const validCryptos = parseValidCryptos(cryptos)

  const selected      = validCryptos.find(c => c.symbol === selectedCoinForChart) ?? validCryptos[0] ?? null
  const total         = validCryptos.length
  const strongest     = [...validCryptos].sort((a, b) => b.energy - a.energy)[0] ?? null
  const positiveCount = validCryptos.filter(c => c.delta > 0).length
  const negativeCount = validCryptos.filter(c => c.delta < 0).length
  const bestSignal    = validCryptos[0] ?? null

  // ============================================
// CHATBOT STATE (adicione junto com os outros useState)
// ============================================
const [chatOpen, setChatOpen] = useState(false)
const [chatMessages, setChatMessages] = useState<Array<{role: string, content: string}>>([])
const [chatInput, setChatInput] = useState("")
const [chatLoading, setChatLoading] = useState(false)

async function sendChatMessage() {
  if (!chatInput.trim() || chatLoading) return
  
  const userMsg = { role: "user", content: chatInput }
  setChatMessages(prev => [...prev, userMsg])
  setChatInput("")
  setChatLoading(true)
  
  try {
    const response = await fetch(`${API_BASE_URL}/chatbot`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ 
        pergunta: chatInput, 
        moeda: selectedCoinForChart 
      })
    })
    const data = await response.json()
    setChatMessages(prev => [...prev, { role: "assistant", content: data.resposta || "Desculpe, não consegui processar." }])
  } catch {
    setChatMessages(prev => [...prev, { role: "assistant", content: "❌ Erro ao conectar com o assistente. Verifique se o servidor está rodando." }])
  } finally {
    setChatLoading(false)
  }
}

  

  // ============================================
  // EFFECTS
  // ============================================

  // Persiste moedas selecionadas no localStorage
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      try {
        const coins = JSON.parse(saved)
        if (Array.isArray(coins) && coins.length > 0) setSelectedCoins(coins)
      } catch {}
    }
  }, [])

  useEffect(() => {
    if (selectedCoins.length > 0) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(selectedCoins))
    }
  }, [selectedCoins])

  // Se a moeda selecionada no gráfico desapareceu (foi removida), troca para a primeira disponível
  useEffect(() => {
    if (total > 0 && !validCryptos.find(c => c.symbol === selectedCoinForChart)) {
      setSelectedCoinForChart(validCryptos[0].symbol)
    }
  }, [validCryptos, selectedCoinForChart, total])

  // Polling de acurácias a cada 5 s
  useEffect(() => {
    fetchAllAccuracies()
    const interval = setInterval(fetchAllAccuracies, 5000)
    return () => clearInterval(interval)
  }, [])

  // Atualiza acurácias quando o número de moedas muda
  useEffect(() => {
    if (total > 0) fetchAllAccuracies()
  }, [total])


  useEffect(() => {
    if (total > 0 && !isRunning) {
      showNotification(`${total} moeda(s) carregada(s). Clique em INICIAR para começar.`, "info")
    }
  }, [total, isRunning])

  // Aviso de saída quando IA está rodando
  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (!isRunning) return
      e.preventDefault()
      e.returnValue = "A IA ainda está rodando. Tem certeza?"
    }
    window.addEventListener("beforeunload", handler)
    return () => window.removeEventListener("beforeunload", handler)
  }, [isRunning])

  useEffect(() => {
  if (selected) {
    console.log("📊 PREVISÕES PARA O GRÁFICO:", {
      symbol: selected.symbol,
      prediction5s: selected.previsao_5s,
      prediction15s: selected.previsao_15s,
      prediction30s: selected.previsao_30s,
      prediction60s: selected.previsao_60s,
    })
    console.log("🔍 DADOS RECEBIDOS DO BACKEND:", {
      symbol: selected.symbol,
      previsao_5s: (selected as any).previsao_5s,
      previsao_15s: (selected as any).previsao_15s,
      previsao_30s: (selected as any).previsao_30s,
      previsao_60s: (selected as any).previsao_60s,
    })
  }
}, [selected])

  // ⭐ Persistir isRunning no localStorage para não perder ao trocar aba
  useEffect(() => {
    const saved = localStorage.getItem("trader_is_running")
    if (saved === "true" && total > 0) {
      setIsRunning(true)
      if (resumePolling) resumePolling()
    }
  }, [total])

  useEffect(() => {
    localStorage.setItem("trader_is_running", String(isRunning))
  }, [isRunning])

  // Adicione este log para debug
useEffect(() => {
  if (selected) {
    console.log("🔍 PREVISÕES REAIS:", {
      symbol: selected.symbol,
      previsao_5s: selected.previsao_5s,
      previsao_15s: selected.previsao_15s,
      previsao_60s: selected.previsao_60s,
      previsao_300s: selected.previsao_300s,
    })
  }
}, [selected])

  // ============================================
  // HELPERS
  // ============================================

  function showNotification(message: string, type: "success" | "error" | "info") {
    setNotification({ message, type })
    setTimeout(() => setNotification(null), 3000)
  }

  async function fetchAllAccuracies() {
    try {
      const result = await executeCommand("crypto report")
      const clean  = typeof result === "string" ? result.replace(/^rse>\s*/, "") : result
      const parsed = JSON.parse(clean)
      if (!Array.isArray(parsed)) return

      const cache: typeof accuracyCache = {}
      parsed.forEach((coin: ReportCoin) => {
        cache[coin.symbol] = { acuracia: coin.acuracia, acertos: coin.acertos, total: coin.total }
      })
      setAccuracyCache(cache)
    } catch {}
  }

  async function fetchPerformanceReport() {
    setIsLoadingReport(true)
    try {
      const result = await executeCommand("crypto report")
      const clean  = typeof result === "string" ? result.replace(/^rse>\s*/, "") : result
      const parsed = JSON.parse(clean)
      setReportData(Array.isArray(parsed) ? parsed : [])
      setSelectedCoinsToRemove([])
      setShowReportModal(true)
    } catch {
      showNotification("Erro ao gerar relatório de desempenho", "error")
    } finally {
      setIsLoadingReport(false)
    }
  }

  // ============================================
  // REMOVE HELPERS
  // ── Toda remoção segue o mesmo padrão:
  //   1. Chama o backend
  //   2. Avisa o pai via onCoinsRemoved (ele atualiza a blacklist)
  //   3. Atualiza selectedCoins / localStorage
  //   4. Força re-render do gráfico
  // ============================================

  async function doRemove(symbolsToRemove: string[]) {
    await executeCommand(`crypto remove ${symbolsToRemove.join(" ")}`)

    // Avisa o pai — ele vai filtrar `units` e a prop `cryptos` chegará limpa
    if (onCoinsRemoved) onCoinsRemoved(symbolsToRemove)

    const remaining = selectedCoins.filter(c => !symbolsToRemove.includes(c))
    setSelectedCoins(remaining)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(remaining))

    setChartKey(prev => prev + 1)
  }

  async function removeSelectedCoins() {
    if (selectedCoinsToRemove.length === 0) {
      showNotification("Nenhuma moeda selecionada para remover", "info")
      return
    }
    setLoading("remove")
    try {
      await doRemove(selectedCoinsToRemove)
      showNotification(`${selectedCoinsToRemove.length} moeda(s) removidas`, "success")
      setShowReportModal(false)
    } catch {
      showNotification("Erro ao remover moedas", "error")
    } finally {
      setLoading(null)
    }
  }

  async function keepOnlySelectedCoins() {
    const toRemove = reportData.map(c => c.symbol).filter(c => !selectedCoinsToRemove.includes(c))
    if (toRemove.length === 0) {
      showNotification("Nenhuma moeda para remover", "info")
      return
    }
    setLoading("keep")
    try {
      await doRemove(toRemove)
      showNotification(
        `Mantidas ${selectedCoinsToRemove.length} moedas. Removidas: ${toRemove.join(", ")}`,
        "success"
      )
      setShowReportModal(false)
    } catch {
      showNotification("Erro ao remover moedas", "error")
    } finally {
      setLoading(null)
    }
  }

  async function clearSelectedCoins() {
    if (coinsToClear.length === 0) {
      showNotification("Nenhuma moeda selecionada para remover", "info")
      return
    }
    setLoading("clear")
    try {
      await doRemove(coinsToClear)
      showNotification(`${coinsToClear.length} moeda(s) removidas`, "success")
      setShowClearCoinsModal(false)
      setCoinsToClear([])
    } catch {
      showNotification("Erro ao remover moedas", "error")
    } finally {
      setLoading(null)
    }
  }

  // ============================================
  // COMMANDS
  // ============================================

  async function handleCommand(command: string, buttonId: string) {
    setLoading(buttonId)

    // START
    
  if (command.includes("start")) {
    if (total === 0) {
      showNotification("Carregue moedas antes de iniciar a IA", "error")
      setLoading(null)
      return
    }
    setIsRunning(true)
    if (resumePolling) resumePolling()
    try {
      await executeCommand(command)  // Sempre chama crypto start
      showNotification("IA iniciada. Monitorando mercado em tempo real.", "success")
    } catch {
      showNotification("Erro ao iniciar IA", "error")
    }
    setLoading(null)
    return
  }

    // STOP
    if (command.includes("stop")) {
      setIsRunning(false)
      try {
        await executeCommand(command)
        await fetchPerformanceReport()
        showNotification("IA parada. Relatório de desempenho gerado.", "info")
      } catch {
        showNotification("Erro ao parar IA", "error")
      }
      setLoading(null)
      return
    }

    // outros
    try {
      await executeCommand(command)

      if (command.includes("spawn")) {
        setIsRunning(false)
        showNotification(`${selectedCoins.length} moeda(s) carregadas.`, "success")
        if (resumePolling) resumePolling()
        localStorage.setItem(STORAGE_KEY, JSON.stringify(selectedCoins))
        if (onRefresh) await onRefresh()
        setChartKey(prev => prev + 1)
        setLoading(null)
        return
      }

      if (command.includes("signal")) {
        if (bestSignal) {
          const signal = getSignalAction(bestSignal.previsao)
          showNotification(
            `SINAL: ${signal.text} ${bestSignal.symbol.replace("USDT", "")} - Confiança: ${Math.abs(bestSignal.previsao).toFixed(0)}%`,
            "info"
          )
        } else {
          showNotification("Carregue moedas primeiro para obter sinais", "info")
        }
      }
    } catch {
      showNotification("Erro ao executar comando", "error")
    } finally {
      setLoading(null)
    }
  }

  // ============================================
  // RENDER
  // ============================================

  return (
    <div className="space-y-4">
      {/* Notificação */}
      {notification && (
        <div className={cn("fixed bottom-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg text-sm",
          notification.type === "success" && "bg-green-500/20 border border-green-500/30 text-green-400",
          notification.type === "error" && "bg-red-500/20 border border-red-500/30 text-red-400",
          notification.type === "info" && "bg-blue-500/20 border border-blue-500/30 text-blue-400"
        )}>
          {notification.message}
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold">Crypto Trading</h2>
          <p className="text-xs text-muted-foreground">
            {total} moeda(s) ativa(s) • {selected?.symbol?.replace("USDT", "") || "BTC"} selecionada
          </p>
        </div>
        {isRunning && (
          <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-green-500/20 text-green-400 border border-green-500/30">
            <Activity className="h-3 w-3" /> AO VIVO
          </span>
        )}
      </div>

      {/* PREVISÕES 10 HORIZONTES */}
      {/* PREVISÕES 10 HORIZONTES - Dados REAIS do dashboard/realtime */}
      {realtimeData?.moedas && (() => {
        const moedaRT = realtimeData.moedas.find(
          (m: any) => m.symbol === selected?.symbol?.replace("USDT", "")
        )
        if (!moedaRT) return null
        
        return (
          <div className="rounded-xl border border-border/50 bg-card/30 p-4">
            <div className="text-xs font-medium text-muted-foreground mb-3">PREVISÕES POR HORIZONTE</div>
            <div className="grid grid-cols-5 gap-2">
              {[
                { time: "5s", value: moedaRT.previsoes?.['5s'] ?? 0 },
                { time: "15s", value: moedaRT.previsoes?.['15s'] ?? 0 },
                { time: "30s", value: moedaRT.previsoes?.['30s'] ?? 0 },
                { time: "60s", value: moedaRT.previsoes?.['60s'] ?? 0 },
                { time: "5min", value: moedaRT.previsoes?.['5min'] ?? 0 },
                { time: "15min", value: moedaRT.previsoes?.['15min'] ?? 0 },
                { time: "30min", value: moedaRT.previsoes?.['30min'] ?? 0 },
                { time: "1h", value: moedaRT.previsoes?.['1h'] ?? 0 },
                { time: "5h", value: moedaRT.previsoes?.['5h'] ?? 0 },
                { time: "1d", value: moedaRT.previsoes?.['1d'] ?? 0 },
              ].map((pred, i) => {
                const isPositive = pred.value >= 0
                const precoAlvo = moedaRT.price * (1 + pred.value / 100)
                return (
                  <div key={i} className={`rounded-lg p-2 text-center border ${isPositive ? 'border-green-500/20 bg-green-500/5' : 'border-red-500/20 bg-red-500/5'}`}>
                    <div className="text-[10px] text-muted-foreground">{pred.time}</div>
                    <div className={`text-sm font-bold font-mono ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
                      {pred.value > 0 ? "+" : ""}{pred.value.toFixed(2)}%
                    </div>
                    <div className="text-[9px] text-muted-foreground">${precoAlvo.toLocaleString(undefined, {maximumFractionDigits: 0})}</div>
                  </div>
                )
              })}
            </div>
          </div>
        )
      })()}

      {/* Timeframes + Tipo de gráfico */}
      <div className="flex items-center justify-between">
        <div className="flex gap-1">
          {[5, 10, 30, 60].map(tf => (
            <button key={tf} onClick={() => setTimeframe(tf)}
              className={cn("px-3 py-1 rounded-md text-xs font-medium", timeframe === tf ? "bg-amber-500/20 text-amber-400 border border-amber-500/30" : "bg-secondary/50 text-muted-foreground")}>
              {tf}s
            </button>
          ))}
        </div>
        <div className="flex gap-1">
          {(["candlestick","line","area"] as const).map(type => (
            <button key={type} onClick={() => setChartType(type)}
              className={cn("px-3 py-1 rounded-md text-xs", chartType === type ? "bg-purple-500/20 text-purple-400" : "text-muted-foreground")}>
              {{ candlestick: "Velas", line: "Linha", area: "Área" }[type]}
            </button>
          ))}
        </div>
      </div>

                  {/* Estado 1: Nenhuma moeda carregada */}
      {total === 0 && (
        <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-8 text-center">
          <p className="text-amber-400 font-medium">Nenhuma moeda carregada</p>
          <p className="text-xs text-muted-foreground mt-2">
            Clique em CARREGAR para selecionar as moedas que deseja analisar.
          </p>
        </div>
      )}

      {/* Estado 2: Moedas carregadas, mas IA não iniciada */}
      {total > 0 && !isRunning && (
        <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-8 text-center">
          <p className="text-amber-400 font-medium">Sistema parado</p>
          <p className="text-xs text-muted-foreground mt-2">
            Clique em INICIAR IA para começar o monitoramento em tempo real.
          </p>
        </div>
      )}

      {/* Estado 3: IA rodando, mas gráfico ainda carregando */}
      {total > 0 && isRunning && (!selected?.candles || selected.candles.length === 0) && (
        <div className="rounded-lg border border-border/50 bg-secondary/20 p-8 text-center">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-cyan-400 mx-auto mb-3" />
          <p className="text-sm text-muted-foreground">Carregando dados do gráfico...</p>
        </div>
      )}

      {/* Estado 4: IA rodando e gráfico pronto */}
      {total > 0 && isRunning && selected && selected.candles && selected.candles.length > 0 && (
        <div className="rounded-lg border border-border/50 bg-secondary/20 p-2">
          <TradingChart
            key={`${selected.symbol}`}
            candles={selected.candles}
            currentPrice={selected.price}
            prediction={selected.previsao}
            prediction5s={selected.previsao_5s}
            prediction15s={selected.previsao_15s}
            prediction30s={selected.previsao_30s}
            prediction60s={selected.previsao_60s}
            prediction300s={selected.previsao_300s}
            prediction900s={selected.previsao_900s}
            prediction1800s={selected.previsao_1800s}
            prediction3600s={selected.previsao_3600s}
            prediction18000s={selected.previsao_18000s}
            prediction86400s={selected.previsao_86400s}
            timeframe={timeframe}
            symbol={selected.symbol}
            isActive={isRunning}
            chartType={chartType}
            showIndicators={showIndicators}
          />
        </div>
      )}


      {/* Seletor de moedas */}
      <div className="flex flex-wrap gap-1">
        {validCryptos
          .filter((c, index, self) => 
            index === self.findIndex(t => t.symbol === c.symbol)  // ⭐ Remove duplicados
          )
          .map(c => (
            <button key={c.symbol} onClick={() => setSelectedCoinForChart(c.symbol)}
              className={cn("px-3 py-1 rounded-md text-xs font-mono", selectedCoinForChart === c.symbol ? "bg-amber-500/20 text-amber-400 border border-amber-500/30" : "bg-secondary/50 text-muted-foreground")}>
              {c.symbol.replace("USDT", "")}
            </button>
          ))}
      </div>

      {/* Botões de ação - 5 colunas */}
      <div className="grid grid-cols-5 gap-2">
        {/* Botão INICIAR/PARAR dinâmico */}
        <Button 
          onClick={() => handleCommand(isRunning ? "crypto stop" : "crypto start", isRunning ? "stop" : "start")} 
          disabled={loading !== null || total === 0}
          className={cn(
            "text-xs",
            isRunning 
              ? "bg-red-500/20 border border-red-500/30 text-red-400 hover:bg-red-500/30" 
              : "bg-green-500/20 border border-green-500/30 text-green-400 hover:bg-green-500/30"
          )}>
          {isRunning ? (
          <><Square className="h-3 w-3 mr-1" /> PARAR</>
        ) : (
          <><Play className="h-3 w-3 mr-1" /> {total > 0 ? "INICIAR" : "CARREGUE PRIMEIRO"}</>
        )}
        </Button>
        <Button onClick={() => setShowCoinSelector(true)} disabled={loading !== null}
          className="bg-amber-500/20 border border-amber-500/30 text-amber-400 hover:bg-amber-500/30 text-xs">
          <RefreshCw className="h-3 w-3 mr-1" /> CARREGAR
        </Button>
        {/* ✅ SINAL - chama a IA e mostra resposta */}
        <Button onClick={handleSignalCommand} disabled={loading !== null || total === 0}
          className="bg-purple-500/20 border border-purple-500/30 text-purple-400 hover:bg-purple-500/30 text-xs">
          <Zap className="h-3 w-3 mr-1" /> SINAL
        </Button>
        {/* ✅ REMOVER */}
        <Button onClick={() => { 
          if (total === 0) { showNotification("Nenhuma moeda para remover", "info"); return }
          setCoinsToClear([]); setShowClearCoinsModal(true) 
        }} disabled={loading !== null || total === 0}
          className="bg-gray-500/20 border border-gray-500/30 text-gray-400 hover:bg-gray-500/30 text-xs">
          <Trash2 className="h-3 w-3 mr-1" /> REMOVER
        </Button>
      </div>

      {/* ✅ Resposta do SINAL (aparece abaixo dos botões) */}
      {signalResponse && (
      <div className="rounded-xl border border-cyan-500/30 bg-cyan-500/5 p-4">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
          <span className="text-xs font-medium text-cyan-400">ANÁLISE DA IA</span>
        </div>
        <p className="text-sm text-muted-foreground leading-relaxed">{signalResponse}</p>
      </div>
    )}

    {signalLoading && (
      <div className="rounded-xl border border-cyan-500/20 bg-cyan-500/5 p-4 flex items-center gap-3">
        <div className="flex gap-1.5">
          <div className="w-2 h-2 rounded-full bg-cyan-400 animate-bounce" />
          <div className="w-2 h-2 rounded-full bg-cyan-400 animate-bounce" style={{animationDelay: '0.15s'}} />
          <div className="w-2 h-2 rounded-full bg-cyan-400 animate-bounce" style={{animationDelay: '0.3s'}} />
        </div>
        <span className="text-xs text-cyan-400">Analisando mercado...</span>
      </div>
    )}

      {/* Coin Selector Modal */}
      {showCoinSelector && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
          <div className="bg-secondary rounded-xl p-6 w-96 border border-border shadow-2xl">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-bold">Selecionar Moedas</h3>
              <button onClick={() => setShowCoinSelector(false)} className="text-muted-foreground hover:text-foreground">
                <X className="h-5 w-5" />
              </button>
            </div>
            <p className="text-xs text-muted-foreground mb-3">Selecione as moedas que a IA vai analisar</p>
            <div className="grid grid-cols-2 gap-2 max-h-64 overflow-y-auto mb-4">
              {availableCoins.map(coin => (
                <label key={coin} className="flex items-center gap-2 p-2 rounded hover:bg-secondary/50 cursor-pointer">
                  <input type="checkbox" checked={selectedCoins.includes(coin)}
                    onChange={e => setSelectedCoins(e.target.checked
                      ? [...selectedCoins, coin]
                      : selectedCoins.filter(c => c !== coin))}
                    className="rounded border-border" />
                  <span className="text-sm font-mono">{coin}</span>
                </label>
              ))}
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowCoinSelector(false)}>Cancelar</Button>
              <Button onClick={async () => {
                setShowCoinSelector(false)
                setLoading("spawn")
                const command = `crypto spawn ${selectedCoins.join(" ")}`
                await executeCommand(command)
                if (onRefresh) await onRefresh()
                setLoading(null)
                showNotification(`${selectedCoins.length} moeda(s) carregadas`, "success")
              }} className="bg-amber-500/20 text-amber-400 hover:bg-amber-500/30">
                Carregar ({selectedCoins.length})
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Clear Coins Modal */}
      {showClearCoinsModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
          <div className="bg-secondary rounded-xl p-6 w-[500px] max-w-[90vw] max-h-[80vh] overflow-y-auto border border-border shadow-2xl">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-bold">REMOVER MOEDAS</h3>
              <button onClick={() => setShowClearCoinsModal(false)} className="text-muted-foreground hover:text-foreground">
                <X className="h-5 w-5" />
              </button>
            </div>
            <p className="text-xs text-muted-foreground mb-3">Selecione as moedas que deseja remover da lista</p>
            <div className="space-y-2 max-h-64 overflow-y-auto mb-4">
              {validCryptos.map(coin => (
                <label key={coin.symbol} className="flex items-center gap-3 p-3 rounded-lg bg-secondary/30 border border-border/50 cursor-pointer hover:bg-secondary/50">
                  <input type="checkbox" checked={coinsToClear.includes(coin.symbol)}
                    onChange={e => setCoinsToClear(e.target.checked
                      ? [...coinsToClear, coin.symbol]
                      : coinsToClear.filter(c => c !== coin.symbol))}
                    className="rounded border-border w-4 h-4" />
                  <div className="flex-1">
                    <div className="font-bold text-foreground">{coin.symbol.replace("USDT", "")}</div>
                    <div className="text-xs text-muted-foreground">
                      Preço: ${coin.price.toFixed(2)} | Variação: {coin.delta > 0 ? "+" : ""}{coin.delta.toFixed(2)}%
                    </div>
                  </div>
                  <div className={cn("text-xs font-bold px-2 py-1 rounded",
                    coin.delta > 0 ? "text-green-400 bg-green-500/20" : "text-red-400 bg-red-500/20")}>
                    {coin.delta > 0 ? "↑" : "↓"} {Math.abs(coin.delta).toFixed(2)}%
                  </div>
                </label>
              ))}
            </div>
            <div className="flex gap-3 mt-6 pt-4 border-t border-border">
              <Button onClick={() => setCoinsToClear(validCryptos.map(c => c.symbol))}
                className="flex-1 bg-yellow-500/20 text-yellow-400 hover:bg-yellow-500/30 border border-yellow-500/30">
                SELECIONAR TODAS
              </Button>
              <Button onClick={() => setCoinsToClear([])}
                className="flex-1 bg-gray-500/20 text-gray-400 hover:bg-gray-500/30 border border-gray-500/30">
                DESMARCAR TUDO
              </Button>
            </div>
            <div className="flex gap-3 mt-3">
              <Button variant="outline" onClick={() => setShowClearCoinsModal(false)} className="flex-1">Cancelar</Button>
              <Button onClick={clearSelectedCoins} disabled={coinsToClear.length === 0}
                className="flex-1 bg-red-500/20 text-red-400 hover:bg-red-500/30 border border-red-500/30">
                REMOVER ({coinsToClear.length})
              </Button>
            </div>
          </div>
        </div>
      )}


      {/* Performance Report Modal */}
      {showReportModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 overflow-auto">
          <div className="bg-secondary rounded-xl p-6 w-[600px] max-w-[90vw] max-h-[80vh] overflow-y-auto border border-border shadow-2xl">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-bold">RELATÓRIO DE DESEMPENHO</h3>
              <button onClick={() => setShowReportModal(false)} className="text-muted-foreground hover:text-foreground">
                <X className="h-5 w-5" />
              </button>
            </div>

            {isLoadingReport ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-400 mx-auto" />
                <p className="text-sm text-muted-foreground mt-2">Analisando desempenho...</p>
              </div>
            ) : reportData.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-muted-foreground">Nenhuma moeda com dados suficientes para análise</p>
              </div>
            ) : (
              <>
                {(["recommended","learning","bad"] as const).map(cat => {
                  const coins = reportData.filter(c => c.categoria === cat)
                  if (coins.length === 0) return null
                  const cfg = {
                    recommended: { label: "MOEDAS RECOMENDADAS (Acurácia ≥ 55%)",    color: "green",  cls: "text-green-400",  bg: "bg-green-500/10  border-green-500/30" },
                    learning:    { label: "MOEDAS EM APRENDIZADO (45-55%)",           color: "yellow", cls: "text-yellow-400", bg: "bg-yellow-500/10 border-yellow-500/30" },
                    bad:         { label: "MOEDAS COM DESEMPENHO BAIXO (≤ 45%)",      color: "red",    cls: "text-red-400",    bg: "bg-red-500/10    border-red-500/30" },
                  }[cat]
                  return (
                    <div key={cat} className="mb-4">
                      <h4 className={cn("text-sm font-bold mb-2", cfg.cls)}>{cfg.label}</h4>
                      <div className="space-y-2">
                        {coins.map(coin => (
                          <div key={coin.symbol} className={cn("flex items-center justify-between p-3 rounded-lg border", cfg.bg)}>
                            <div>
                              <div className="font-bold text-foreground">{coin.symbol.replace("USDT", "")}</div>
                              <div className="text-xs text-muted-foreground">{coin.acertos} acertos / {coin.erros} erros</div>
                            </div>
                            <div className="text-right">
                              <div className={cn("font-bold", cfg.cls)}>{coin.acuracia}%</div>
                              <div className={cn("text-xs", cfg.cls)}>
                                {{ recommended: "Recomendada", learning: "Em aprendizado", bad: "Desempenho baixo" }[cat]}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )
                })}

                <div className="flex gap-3 mt-6 pt-4 border-t border-border">
                  <Button onClick={() => setShowReportModal(false)}
                    className="flex-1 bg-amber-500/20 text-amber-400 hover:bg-amber-500/30 border border-amber-500/30">
                    FECHAR RELATÓRIO
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground text-center mt-3">
                  Moedas com acurácia acima de 55% são recomendadas. Abaixo de 45% considere remover.
                </p>
              </>
            )}
          </div>
        </div>
      )}

      {/* Empty state */}
      {total === 0 && (
        <div className="text-center py-10 text-muted-foreground">
          <p>Nenhuma moeda carregada</p>
          <p className="text-xs mt-2">Clique em CARREGAR para selecionar moedas</p>
        </div>
      )}
    </div>
  )
}