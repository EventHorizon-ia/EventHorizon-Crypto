import { useEffect, useRef, useState, useMemo } from "react"
import {
  createChart, CrosshairMode, LineStyle,
  IChartApi, ISeriesApi, UTCTimestamp,
  CandlestickSeries, LineSeries, AreaSeries,
} from "lightweight-charts"

interface Candle {
  time: number; open: number; high: number; low: number; close: number
}

// No arquivo TradingChart.tsx, atualize a interface:
interface TradingChartProps {
  candles: Candle[]
  currentPrice: number
  prediction: number
  prediction5s?: number
  prediction15s?: number
  prediction30s?: number
  prediction60s?: number
  // ✅ NOVOS HORIZONTES
  prediction300s?: number
  prediction900s?: number
  prediction1800s?: number
  prediction3600s?: number
  prediction18000s?: number
  prediction86400s?: number
  // ✅ CONSENSO
  consensoCurto?: number
  consensoMedio?: number
  consensoLongo?: number
  timeframe?: number
  symbol?: string
  isActive?: boolean
  chartType?: "candlestick" | "line" | "area"
  showIndicators?: boolean
}

function safeTime(t: any): UTCTimestamp { return Math.floor(Number(t)) as UTCTimestamp }

function formatBRTime(unixSeconds: number): string {
  return new Date(unixSeconds * 1000).toLocaleString("pt-BR", {
    timeZone: "America/Sao_Paulo",
    day: "2-digit", month: "2-digit", year: "2-digit",
    hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false,
  })
}

function calcEMA(data: Candle[], period: number) {
  const k = 2 / (period + 1)
  let ema = data[0]?.close ?? 0
  return data.map(c => {
    ema = c.close * k + ema * (1 - k)
    return { time: safeTime(c.time), value: parseFloat(ema.toFixed(4)) }
  })
}

function calcBollinger(data: Candle[], period = 20, mult = 2) {
  const upper: any[] = [], lower: any[] = [], mid: any[] = []
  for (let i = period - 1; i < data.length; i++) {
    const slice = data.slice(i - period + 1, i + 1).map(c => c.close)
    const mean = slice.reduce((a, b) => a + b, 0) / period
    const sd = Math.sqrt(slice.reduce((a, b) => a + (b - mean) ** 2, 0) / period)
    const t = safeTime(data[i].time)
    upper.push({ time: t, value: parseFloat((mean + mult * sd).toFixed(4)) })
    lower.push({ time: t, value: parseFloat((mean - mult * sd).toFixed(4)) })
    mid.push({ time: t, value: parseFloat(mean.toFixed(4)) })
  }
  return { upper, lower, mid }
}

function calcRSI(data: Candle[], period = 14): number {
  if (data.length < period + 1) return 50
  const closes = data.slice(-(period + 1)).map(c => c.close)
  let gains = 0, losses = 0
  for (let i = 1; i < closes.length; i++) {
    const d = closes[i] - closes[i - 1]
    if (d >= 0) gains += d; else losses -= d
  }
  return parseFloat((100 - 100 / (1 + gains / (losses || 1))).toFixed(2))
}

// Seeds baseadas apenas no bucketBase — estáveis durante o bucket inteiro
function gerarVelasFuturas(
  price: number,
  bucketBase: number,
  preds: { time: number; value: number }[],
  atr: number
): Candle[] {
  // ⭐ CORREÇÃO: Escala as previsões para torná-las VISÍVEIS
  // O valor original é em percentual (ex: 0.01 = 0.01%)
  // Multiplicamos por 10 para ter 0.1% de movimento mínimo VISÍVEL
  
  const minVisibleMovement = price * 0.001 // 0.1% do preço (mínimo para ser visível)
  const baseVol = Math.max(atr, price * 0.001)

  return preds.map((pred, i) => {
    const seed = (((bucketBase + pred.time) * (i + 13) * 811) % 1009) / 1009
    
    // ⭐ ESCALA a previsão para ter pelo menos 0.1% de movimento
    let movementPercent = Math.abs(pred.value)
    
    // Se o movimento for muito pequeno (< 0.05%), escala para 0.1% - 0.3%
    if (movementPercent < 0.05) {
      movementPercent = 0.1 + (seed * 0.2)  // Entre 0.1% e 0.3%
    }
    
    const bodyValue = price * (movementPercent / 100)
    const direction = pred.value >= 0 ? 1 : -1
    
    const open = price
    const close = price + direction * Math.max(bodyValue, minVisibleMovement)

    const wickHigh = baseVol * (0.4 + seed * 0.4) + Math.abs(close - open) * 0.3
    const wickLow = baseVol * (0.3 + (1 - seed) * 0.4) + Math.abs(close - open) * 0.2

    return {
      time: bucketBase + pred.time,
      open,
      high: Math.max(open, close) + wickHigh,
      low: Math.min(open, close) - wickLow,
      close,
    }
  })
}

function gerarLinhaFutura(
  price: number,
  bucketBase: number, // agora recebe já o próximo bucket
  preds: { time: number; value: number }[]
): { time: UTCTimestamp; value: number }[] {
  return [
    { time: safeTime(bucketBase), value: price }, // âncora no início do próximo bucket
    ...preds.map(p => ({
      time: safeTime(bucketBase + p.time),
      value: price * (1 + p.value / 100)
    })),
  ]
}

export function TradingChart({
  candles, currentPrice, prediction,
  prediction5s, prediction15s, prediction30s, prediction60s,
  prediction300s, prediction900s, prediction1800s, 
  prediction3600s, prediction18000s, prediction86400s,
  consensoCurto, consensoMedio, consensoLongo,
  timeframe = 5, symbol = "BTCUSDT", isActive = true,
  chartType = "candlestick", showIndicators = true,
}: TradingChartProps) {
  const containerRef      = useRef<HTMLDivElement>(null)
  const containerOuterRef = useRef<HTMLDivElement>(null)
  const chartRef          = useRef<IChartApi | null>(null)
  const candleSeriesRef   = useRef<ISeriesApi<"Candlestick"> | ISeriesApi<"Line"> | ISeriesApi<"Area"> | null>(null)
  const ema9Ref           = useRef<ISeriesApi<"Line"> | null>(null)
  const ema21Ref          = useRef<ISeriesApi<"Line"> | null>(null)
  const bbUpperRef        = useRef<ISeriesApi<"Line"> | null>(null)
  const bbLowerRef        = useRef<ISeriesApi<"Line"> | null>(null)
  const bbMidRef          = useRef<ISeriesApi<"Line"> | null>(null)
  const futureCandlesRef  = useRef<ISeriesApi<"Candlestick"> | null>(null)
  const futureLineRef     = useRef<ISeriesApi<"Line"> | null>(null)
  const futureCandleTimesRef = useRef<Map<number, { label: string; price: number; change: number }>>(new Map())
  // Adicione junto com os outros useState no topo do componente
  const [chartVersion, setChartVersion] = useState(0)
  const animIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const targetPriceRef  = useRef(currentPrice)
  const animPriceRef    = useRef(currentPrice)

  // Vela em construção: acumula high/low REAL tick a tick
  // Isso é o que dá pavios verdadeiros (range de preço no período)
  const liveCandleRef = useRef<{
    bucket: number; open: number; high: number; low: number
  } | null>(null)

  // Refs estáveis para closures do interval
  const candlesRef = useRef(candles)
  const tfRef      = useRef(timeframe)
  const ctRef      = useRef(chartType)
  const isFirstFutureDataRef = useRef(true)
  useEffect(() => { candlesRef.current = candles }, [candles])
  useEffect(() => { tfRef.current = timeframe    }, [timeframe])
  useEffect(() => { ctRef.current = chartType    }, [chartType])

  const [hoverOHLC,    setHoverOHLC]    = useState<Candle | null>(null)
  const [rsi,          setRsi]          = useState(50)
  const [lastPrice,    setLastPrice]    = useState<number | null>(null)
  const [priceChange,  setPriceChange]  = useState(0)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [futureTooltip, setFutureTooltip] = useState<{
    x: number; y: number; visible: boolean
    label: string; price: number; change: number; time: string
  }>({ x: 0, y: 0, visible: false, label: "", price: 0, change: 0, time: "" })

 // ⭐ ESTABILIZAR predictions - só atualiza quando valores REALMENTE mudam
const predictionsRef = useRef<Array<{time: number, value: number}>>([])

const stablePredictions = useMemo(() => {
  const prev = predictionsRef.current
  const next = [
    { time: 5,     value: prediction5s     ?? prediction },
    { time: 15,    value: prediction15s    ?? prediction },
    { time: 30,    value: prediction30s    ?? prediction },
    { time: 60,    value: prediction60s    ?? prediction },
    { time: 300,   value: prediction300s   ?? prediction },
    { time: 900,   value: prediction900s   ?? prediction },
    { time: 1800,  value: prediction1800s  ?? prediction },
    { time: 3600,  value: prediction3600s  ?? prediction },
    { time: 18000, value: prediction18000s ?? prediction },
    { time: 86400, value: prediction86400s ?? prediction },
  ]
  
  // Só troca a referência se algum valor REALMENTE mudou
  if (prev.length === 0) {
    predictionsRef.current = next
    return next
  }
  
  const changed = next.some((n, i) => 
    !prev[i] || Math.abs(n.value - prev[i].value) > 0.0001
  )
  
  if (!changed) return prev
  predictionsRef.current = next
  return next
}, [prediction, prediction5s, prediction15s, prediction30s, prediction60s,
    prediction300s, prediction900s, prediction1800s, prediction3600s,
    prediction18000s, prediction86400s])

  const atr = useMemo(() => {
    const w = candles.slice(-14)
    if (w.length === 0) return currentPrice * 0.001
    const vals = w.map(c => c.high - c.low)
    return vals.reduce((a, b) => a + b, 0) / vals.length
  }, [candles, currentPrice])

  // ── Fullscreen ─────────────────────────────────────────────────────────
  useEffect(() => {
    const handler = () => {
      const fs = !!document.fullscreenElement
      setIsFullscreen(fs)
      setTimeout(() => {
        chartRef.current?.applyOptions({
          width:  containerRef.current?.clientWidth || 0,
          height: fs ? window.innerHeight - 180 : 600,
        })
      }, 100)
    }
    document.addEventListener("fullscreenchange", handler)
    return () => document.removeEventListener("fullscreenchange", handler)
  }, [])

  useEffect(() => { targetPriceRef.current = currentPrice }, [currentPrice])

  // ── Animação: high/low real acumulado no liveCandleRef ─────────────────
  useEffect(() => {
    if (!isActive) {
      if (animIntervalRef.current) clearInterval(animIntervalRef.current)
      animIntervalRef.current = null
      return
    }
    if (animIntervalRef.current) clearInterval(animIntervalRef.current)

    // ── FIX BUG 2: pausa/retoma o interval quando a aba perde/ganha foco ──
    const handleVisibilityChange = () => {
      if (document.hidden) {
        // Aba em background: para o interval para não acumular ticks perdidos
        if (animIntervalRef.current) {
          clearInterval(animIntervalRef.current)
          animIntervalRef.current = null
        }
      } else {
        // Aba voltou ao foco: sincroniza o preço animado com o alvo atual
        // e religa o interval limpo
        animPriceRef.current = targetPriceRef.current
        if (!animIntervalRef.current && isActive) {
          startAnimInterval()
        }
        // Força resize para o chart recalcular dimensões (pode ter mudado)
        if (chartRef.current && containerRef.current) {
          chartRef.current.applyOptions({
            width: containerRef.current.clientWidth,
          })
        }
      }
    }

    function startAnimInterval() {
      animIntervalRef.current = setInterval(() => {
        if (!candleSeriesRef.current) return

        const diff = targetPriceRef.current - animPriceRef.current
        animPriceRef.current += Math.abs(diff) < 0.01 ? diff : diff * 0.3
        const p = animPriceRef.current

        const now    = Math.floor(Date.now() / 1000)
        const bucket = now - (now % tfRef.current)

        if (ctRef.current === "candlestick") {
          const existing = candlesRef.current.find(c =>
            c.time === bucket || (c.time - (c.time % tfRef.current)) === bucket
          )

          if (existing) {
            // Bucket fechado do backend: usa high/low reais
            candleSeriesRef.current!.update({
              time: safeTime(bucket), open: existing.open,
              high: Math.max(existing.high, p), low: Math.min(existing.low, p), close: p,
            })
            if (liveCandleRef.current?.bucket !== bucket) {
              liveCandleRef.current = { bucket, open: p, high: p, low: p }
            }
          } else {
            // Bucket em construção: acumula high/low real tick a tick
            if (!liveCandleRef.current || liveCandleRef.current.bucket !== bucket) {
              liveCandleRef.current = { bucket, open: p, high: p, low: p }
            } else {
              liveCandleRef.current.high = Math.max(liveCandleRef.current.high, p)
              liveCandleRef.current.low  = Math.min(liveCandleRef.current.low,  p)
            }
            const lc = liveCandleRef.current
            candleSeriesRef.current!.update({
              time: safeTime(bucket), open: lc.open,
              high: lc.high, low: lc.low, close: p,
            })
          }
        } else {
          ;(candleSeriesRef.current as any).update({ time: safeTime(bucket), value: p })
        }

        setLastPrice(p)
      }, 50)
    }

    document.addEventListener("visibilitychange", handleVisibilityChange)
    startAnimInterval()

    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange)
      if (animIntervalRef.current) clearInterval(animIntervalRef.current)
      animIntervalRef.current = null
    }
  }, [isActive])

  // ── FIX BUG 1: removido o useEffect que brigava com autoScale ──────────
  // O useEffect que chamava priceScale("right").applyOptions com autoScale: false
  // e depois true foi removido. Ele causava um "reset" da escala visual a cada
  // atualização de candles, produzindo o efeito de zoom involuntário.
  // A escala agora é controlada apenas pelas opções iniciais do chart (autoScale: true,
  // scaleMargins top/bottom: 0.08) definidas no useEffect de inicialização abaixo.

  // ── Init do chart ──────────────────────────────────────────────────────
  useEffect(() => {
    if (!containerRef.current) return

    const chart = createChart(containerRef.current, {
      layout: {
        background: { color: "#060b14" }, textColor: "#8b9ab0",
        fontFamily: "'JetBrains Mono', 'Fira Code', monospace", fontSize: 11,
      },
      grid: {
        vertLines: { color: "#0d1520", style: LineStyle.Solid },
        horzLines: { color: "#0d1520", style: LineStyle.Solid },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: { color: "#2a3a54", width: 1, style: LineStyle.Dashed, labelBackgroundColor: "#1a2a3a" },
        horzLine: { color: "#2a3a54", width: 1, style: LineStyle.Dashed, labelBackgroundColor: "#1a2a3a" },
      },
      rightPriceScale: {
        borderColor: "#0d1a28",
        scaleMargins: { top: 0.08, bottom: 0.08 },
        textColor: "#4a6a8a",
        autoScale: true,
      },
      timeScale: {
        borderColor: "#0d1a28",
        timeVisible: true,
        secondsVisible: timeframe < 60,
        rightBarStaysOnScroll: true,
        lockVisibleTimeRangeOnResize: true,
        fixRightEdge: false,
        rightOffset: 20,
        tickMarkFormatter: (t: number, tickMarkType: number) => {
          const d = new Date(t * 1000)
          const opts: Intl.DateTimeFormatOptions = { timeZone: "America/Sao_Paulo", hour12: false }
          if (tickMarkType <= 2)  return d.toLocaleDateString("pt-BR",  { ...opts, day: "2-digit", month: "2-digit" })
          if (tickMarkType === 4) return d.toLocaleTimeString("pt-BR",  { ...opts, hour: "2-digit", minute: "2-digit", second: "2-digit" })
          return d.toLocaleTimeString("pt-BR", { ...opts, hour: "2-digit", minute: "2-digit" })
        },
      },
      localization: { timeFormatter: (t: number) => formatBRTime(t) },
      width:  containerRef.current.clientWidth,
      height: 600,
      handleScroll: { mouseWheel: true, pressedMouseMove: true, horzTouchDrag: true },
      handleScale:  { mouseWheel: true, pinch: true, axisPressedMouseMove: true },
    })

    // Série principal
    let main: any
    if (chartType === "candlestick") {
      main = chart.addSeries(CandlestickSeries, {
        upColor: "#00e676", downColor: "#ff3d57",
        borderUpColor: "#00e676", borderDownColor: "#ff3d57",
        wickUpColor: "#00a854", wickDownColor: "#cc2d44",
      })
    } else if (chartType === "line") {
      main = chart.addSeries(LineSeries, {
        color: "#38bdf8", lineWidth: 2, priceLineVisible: true, lastValueVisible: true,
      })
    } else {
      main = chart.addSeries(AreaSeries, {
        topColor: "rgba(0,230,118,0.4)", bottomColor: "rgba(0,230,118,0.0)",
        lineColor: "#00e676", lineWidth: 2, crosshairMarkerVisible: true,
        crosshairMarkerRadius: 4, crosshairMarkerBorderColor: "#00e676",
        crosshairMarkerBackgroundColor: "#1a2a3a",
      })
    }
    candleSeriesRef.current = main

    if (showIndicators) {
      ema9Ref.current    = chart.addSeries(LineSeries, { color: "#f59e0b", lineWidth: 1, priceLineVisible: false, lastValueVisible: false })
      ema21Ref.current   = chart.addSeries(LineSeries, { color: "#38bdf8", lineWidth: 1, priceLineVisible: false, lastValueVisible: false })
      bbUpperRef.current = chart.addSeries(LineSeries, { color: "rgba(100,120,200,0.4)", lineWidth: 1, lineStyle: LineStyle.Dashed })
      bbLowerRef.current = chart.addSeries(LineSeries, { color: "rgba(100,120,200,0.4)", lineWidth: 1, lineStyle: LineStyle.Dashed })
      bbMidRef.current   = chart.addSeries(LineSeries, { color: "rgba(100,120,200,0.2)", lineWidth: 1, lineStyle: LineStyle.Dotted })
    }

    if (chartType === "candlestick") {
      futureCandlesRef.current = chart.addSeries(CandlestickSeries, {
        priceScaleId: "future",
        upColor:        "rgba(0,230,118,0.3)", downColor:       "rgba(255,61,87,0.3)",
        borderUpColor:  "rgba(0,230,118,0.6)", borderDownColor: "rgba(255,61,87,0.6)",
        wickUpColor:    "rgba(0,168,84,0.3)",  wickDownColor:   "rgba(204,45,68,0.3)",
        priceLineVisible: false, lastValueVisible: false,
      })
      chart.priceScale("future").applyOptions({
        scaleMargins: { top: 0.08, bottom: 0.08 },
        visible: false,
        autoScale: true,
      })
    } else {
      futureLineRef.current = chart.addSeries(LineSeries, {
        priceScaleId: "future",
        color: "rgba(0,230,118,0.7)", lineWidth: 2, lineStyle: LineStyle.Dashed,
        priceLineVisible: false, lastValueVisible: false,
        crosshairMarkerVisible: true, crosshairMarkerRadius: 5,
        crosshairMarkerBorderColor: "#00e676", crosshairMarkerBackgroundColor: "#060b14",
      })
      chart.priceScale("future").applyOptions({ visible: false, autoScale: true })
    }

    chartRef.current = chart

    chart.subscribeCrosshairMove((param) => {
      if (!param.point) {
        setFutureTooltip(prev => prev.visible ? { ...prev, visible: false } : prev)
        setHoverOHLC(null)
        return
      }

      if (param.time) {
        const t = typeof param.time === "number" ? Math.floor(param.time) : null
        if (t !== null) {
          const fd = futureCandleTimesRef.current.get(t)
          if (fd) {
            setFutureTooltip({
              visible: true, x: param.point.x, y: param.point.y,
              label: fd.label, price: fd.price, change: fd.change, time: formatBRTime(t),
            })
            setHoverOHLC(null)
            return
          }

          const seriesData = candleSeriesRef.current
            ? (param.seriesData?.get(candleSeriesRef.current as any) as any)
            : null

          if (seriesData && seriesData.open !== undefined) {
            setHoverOHLC({
              time:  safeTime(seriesData.time ?? t),
              open:  seriesData.open,
              high:  seriesData.high,
              low:   seriesData.low,
              close: seriesData.close,
            })
          } else {
            const bucket = t - (t % tfRef.current)
            const candleData = candlesRef.current.find(c =>
              c.time === t || c.time === bucket ||
              Math.floor(c.time / tfRef.current) === Math.floor(t / tfRef.current)
            )
            setHoverOHLC(candleData ?? null)
          }
        } else {
          setHoverOHLC(null)
        }
      } else {
        setHoverOHLC(null)
      }

      setFutureTooltip(prev => prev.visible ? { ...prev, visible: false } : prev)
    })

    const ro = new ResizeObserver(() => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth })
      }
    })
    ro.observe(containerRef.current)

    return () => {
    ro.disconnect()
    if (animIntervalRef.current) clearInterval(animIntervalRef.current)
    chart.remove()
    chartRef.current = candleSeriesRef.current = null
    ema9Ref.current = ema21Ref.current = null
    bbUpperRef.current = bbLowerRef.current = bbMidRef.current = null
    futureCandlesRef.current = futureLineRef.current = null
    // ✅ NOVO: sinaliza que o chart foi recriado
    setChartVersion(v => v + 1)
  }
  }, [timeframe, chartType, showIndicators])

  // ── Dados históricos ───────────────────────────────────────────────────
  // ── Dados históricos (CORRIGIDO - sem reset) ────────────────────────────
// ── Dados históricos (CORRIGIDO - recarrega quando chartType muda) ────────────
const lastCandleTimeRef = useRef<number>(0)
const previousChartTypeRef = useRef(chartType)

useEffect(() => {
  if (!candleSeriesRef.current || candles.length === 0) return

  // ✅ REMOVIDA a lógica de chartTypeChanged — chartVersion já garante o reset
  lastCandleTimeRef.current = 0

  const now = Math.floor(Date.now() / 1000)
  const bucket = now - (now % timeframe)
  const grouped = new Map<number, Candle>()

  for (const c of candles) {
    const b = c.time - (c.time % timeframe)
    if (b >= bucket) continue
    if (!grouped.has(b)) {
      grouped.set(b, { time: b, open: c.open, high: c.high, low: c.low, close: c.close })
    } else {
      const ex = grouped.get(b)!
      ex.high = Math.max(ex.high, c.high)
      ex.low = Math.min(ex.low, c.low)
      ex.close = c.close
    }
  }

  const closed = Array.from(grouped.values()).sort((a, b) => a.time - b.time)
  if (!closed.length) return

  // ✅ Sempre usa setData (lastCandleTimeRef foi zerado acima)
  if (chartType === "candlestick") {
    candleSeriesRef.current.setData(closed.map(c => ({
      time: safeTime(c.time),
      open: c.open,
      high: Math.max(c.high, c.open, c.close),
      low: Math.min(c.low, c.open, c.close),
      close: c.close,
    })))
  } else {
    candleSeriesRef.current.setData(closed.map(c => ({ time: safeTime(c.time), value: c.close })))
  }

  lastCandleTimeRef.current = closed[closed.length - 1]?.time || 0

  setRsi(calcRSI(closed))
  if (closed.length >= 2) {
    const [prev, last] = [closed[closed.length - 2], closed[closed.length - 1]]
    setPriceChange(parseFloat((((last.close - prev.close) / prev.close) * 100).toFixed(3)))
  }
  if (showIndicators) {
    if (ema9Ref.current && closed.length >= 9) ema9Ref.current.setData(calcEMA(closed, 9) as any)
    if (ema21Ref.current && closed.length >= 21) ema21Ref.current.setData(calcEMA(closed, 21) as any)
    if (closed.length >= 20) {
      const bb = calcBollinger(closed)
      bbUpperRef.current?.setData(bb.upper)
      bbLowerRef.current?.setData(bb.lower)
      bbMidRef.current?.setData(bb.mid)
    }
  }
  const cur = candles.find(c => c.time - (c.time % timeframe) === bucket)
  if (cur) animPriceRef.current = cur.close
}, [candles, timeframe, chartType, showIndicators, chartVersion]) // ✅ chartVersion adicionado

  useEffect(() => { animPriceRef.current = currentPrice }, [timeframe, currentPrice, chartVersion])

  // ── Dados das séries futuras ───────────────────────────────────────────
  useEffect(() => {
    if (!chartRef.current || stablePredictions.length === 0) return

    const price      = targetPriceRef.current
    const nowS       = Math.floor(Date.now() / 1000)
    const bucketBase = nowS - (nowS % timeframe)
    const labels     = ["5s", "15s", "30s", "60s", "5m", "15m", "30m", "1h", "5h", "1d"]

    // Captura o range visível ANTES de mexer nos dados
    //const visibleRange = chartRef.current.timeScale().getVisibleRange()

    futureCandleTimesRef.current.clear()

    if (chartType === "candlestick" && futureCandlesRef.current) {
      const velas = gerarVelasFuturas(price, bucketBase, stablePredictions, atr)
      if (!velas.length) return

      velas.forEach((c, i) =>
        futureCandleTimesRef.current.set(safeTime(c.time), {
          label:  `Previsão ${labels[i] ?? `${stablePredictions[i]?.time}s`}`,
          price:  c.close,
          change: ((c.close - price) / price) * 100,
        })
      )

      futureCandlesRef.current.setData(velas.map(c => ({
        time:  safeTime(c.time),
        open:  c.open, high: c.high, low: c.low, close: c.close,
      })))

    } else if (chartType !== "candlestick" && futureLineRef.current) {
      const pts   = gerarLinhaFutura(price, bucketBase, stablePredictions)
      const isPos = stablePredictions.some(p => p.value > 0)
      futureLineRef.current.applyOptions({
        color: isPos ? "rgba(0,230,118,0.7)" : "rgba(255,61,87,0.7)",
        crosshairMarkerBorderColor: isPos ? "#00e676" : "#ff3d57",
      })
      futureLineRef.current.setData(pts)

      stablePredictions.forEach((pred, i) => {
        futureCandleTimesRef.current.set(safeTime(bucketBase + pred.time), {
          label:  `Previsão ${labels[i] ?? `${pred.time}s`}`,
          price:  price * (1 + pred.value / 100),
          change: pred.value,
        })
      })
    }

    // Restaura o range visível após o setData — evita o scroll automático
  }, [stablePredictions, atr, timeframe, chartType])

  // Reset a flag quando o chart for recriado
  useEffect(() => {
    isFirstFutureDataRef.current = true;
  }, [chartType]);

  // ── Render ─────────────────────────────────────────────────────────────
  const displayCandle = hoverOHLC ?? (candles.length ? candles[candles.length - 1] : null)
  const isGreen  = displayCandle ? displayCandle.close >= displayCandle.open : true
  const rsiColor = rsi > 70 ? "#ff3d57" : rsi < 30 ? "#00e676" : "#f59e0b"

  return (
    <div ref={containerOuterRef} className="relative w-full rounded-xl overflow-hidden select-none"
      style={{ background: "#060b14", fontFamily: "'JetBrains Mono', monospace" }}>

      {/* Top Bar */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b" style={{ borderColor: "#0d1a28" }}>
        <div>
          <span className="text-xs font-bold tracking-widest" style={{ color: "#8b9ab0" }}>{symbol}</span>
          {lastPrice !== null && (
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-lg font-bold tabular-nums" style={{ color: isGreen ? "#00e676" : "#ff3d57" }}>
                {lastPrice.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
              <span className="text-xs font-semibold px-1.5 py-0.5 rounded" style={{
                background: priceChange >= 0 ? "rgba(0,230,118,0.12)" : "rgba(255,61,87,0.12)",
                color:      priceChange >= 0 ? "#00e676" : "#ff3d57",
              }}>
                {priceChange >= 0 ? "+" : ""}{priceChange}%
              </span>
            </div>
          )}
        </div>

        {displayCandle && (
          <div className="flex flex-col gap-0.5 text-xs tabular-nums text-right" style={{ color: "#4a6a8a" }}>
            <div className="flex gap-4">
              {(["O","H","L","C"] as const).map((lbl, i) => {
                const v = [displayCandle.open, displayCandle.high, displayCandle.low, displayCandle.close][i]
                return (
                  <span key={lbl}>
                    <span style={{ color: "#2a4a6a" }}>{lbl} </span>
                    <span style={{ color: lbl === "H" ? "#00e676" : lbl === "L" ? "#ff3d57" : "#8b9ab0" }}>
                      {v.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </span>
                  </span>
                )
              })}
            </div>
            <div className="text-[9px]" style={{ color: "#2a4a6a" }}>
              🕐 {formatBRTime(
                displayCandle.time > 1e10
                  ? Math.floor(displayCandle.time / 1000)
                  : displayCandle.time
              )} (Brasília)
            </div>
          </div>
        )}

        <div className="flex items-center gap-2">
          <div className="text-xs px-2 py-1 rounded" style={{ background: "rgba(0,0,0,0.4)", border: "1px solid #0d1a28" }}>
            <span style={{ color: "#2a4a6a" }}>RSI </span>
            <span className="font-bold" style={{ color: rsiColor }}>{rsi}</span>
          </div>
          <div className="text-xs px-2 py-1 rounded" style={{ background: "rgba(0,0,0,0.4)", border: "1px solid #0d1a28" }}>
            <span style={{ color: "#2a4a6a" }}>TF </span>
            <span style={{ color: "#4a8a6a" }}>{timeframe}s</span>
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="flex gap-4 px-4 py-1.5" style={{ background: "rgba(0,0,0,0.3)" }}>
        {[
          { label: "EMA 9",    color: "#f59e0b" },
          { label: "EMA 21",   color: "#38bdf8" },
          { label: "BB(20,2)", color: "rgba(100,120,200,0.6)" },
          { label: "Signal",   color: "#d946ef" },
        ].map(({ label, color }) => (
          <div key={label} className="flex items-center gap-1.5">
            <div className="w-5 h-px" style={{ background: color }} />
            <span className="text-[10px]" style={{ color: "#3a5a7a" }}>{label}</span>
          </div>
        ))}
        <div className="ml-auto flex items-center gap-1.5">
          <div className="w-1.5 h-1.5 rounded-full animate-pulse"
            style={{ background: prediction > 0 ? "#00e676" : prediction < 0 ? "#ff3d57" : "#f59e0b" }} />
          <span className="text-[10px] font-semibold"
            style={{ color: prediction > 0 ? "#00e676" : prediction < 0 ? "#ff3d57" : "#f59e0b" }}>
            {prediction > 1 ? "STRONG BUY" : prediction > 0 ? "BUY" : prediction < -1 ? "STRONG SELL" : prediction < 0 ? "SELL" : "NEUTRAL"}
          </span>
        </div>
      </div>

      {/* Chart */}
      <div className="relative">
        <div ref={containerRef} className="w-full" style={{ height: 500 }} />

        {futureTooltip.visible && (
          <div className="pointer-events-none absolute z-50 rounded-lg px-3 py-2 text-xs"
            style={{
              left: futureTooltip.x + 12, top: futureTooltip.y - 10,
              background: "rgba(6,11,20,0.95)",
              border: `1px solid ${futureTooltip.change >= 0 ? "rgba(0,230,118,0.5)" : "rgba(255,61,87,0.5)"}`,
              boxShadow: `0 4px 20px ${futureTooltip.change >= 0 ? "rgba(0,230,118,0.15)" : "rgba(255,61,87,0.15)"}`,
              fontFamily: "'JetBrains Mono', monospace", minWidth: 160,
            }}>
            <div className="font-bold mb-1" style={{ color: futureTooltip.change >= 0 ? "#00e676" : "#ff3d57" }}>
              {futureTooltip.label}
            </div>
            <div>
              <span style={{ color: "#4a6a8a" }}>Preço: </span>
              <span className="font-semibold" style={{ color: "#c8d8e8" }}>
                {futureTooltip.price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
            </div>
            <div>
              <span style={{ color: "#4a6a8a" }}>Variação: </span>
              <span className="font-semibold" style={{ color: futureTooltip.change >= 0 ? "#00e676" : "#ff3d57" }}>
                {futureTooltip.change >= 0 ? "+" : ""}{futureTooltip.change.toFixed(4)}%
              </span>
            </div>
            <div style={{ color: "#3a5a7a", fontSize: 9, marginTop: 4 }}>
              {futureTooltip.time} (Brasília)
            </div>
          </div>
        )}
      </div>

      {/* RSI Bar */}
      <div className="px-4 py-2 flex items-center gap-3" style={{ background: "#060b14", borderTop: "1px solid #0d1a28" }}>
        <span className="text-[10px] w-6" style={{ color: "#2a4a6a" }}>RSI</span>
        <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: "#0d1a28" }}>
          <div className="h-full rounded-full transition-all duration-500"
            style={{ width: `${rsi}%`, background: "linear-gradient(90deg, #00e676 0%, #f59e0b 50%, #ff3d57 100%)" }} />
        </div>
        <div className="flex gap-4 text-[9px]" style={{ color: "#1a3a5a" }}>
          <span style={{ color: "#00a854" }}>OS 30</span><span>50</span><span style={{ color: "#cc2d44" }}>OB 70</span>
        </div>
      </div>

      {/* Watermark */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none select-none text-center" style={{ opacity: 0.02 }}>
        <div className="text-7xl font-black tracking-widest whitespace-nowrap" style={{ color: "#fff" }}>
          {symbol.replace("USDT", "")}
        </div>
      </div>
    </div>
  )
}