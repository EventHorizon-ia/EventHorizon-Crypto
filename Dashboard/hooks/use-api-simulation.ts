"use client"

import { useCallback, useEffect, useState } from "react"
import { API_BASE_URL } from '@/lib/api';

const MAX_ITEMS = 50

const POLL_INTERVAL = (() => {
  try {
    const config = JSON.parse(localStorage.getItem("trader_config") || "{}")
    return (config.frequenciaAtualizacao || 5) * 1000
  } catch {
    return 5000
  }
})()

interface ApiStatus {
  energia_total: number
  dados: Array<{
    id: string
    energia: number
    estado: string
    symbol?: string
    price?: number
    delta?: number
    tipo?: string
    previsao?: number
    previsao_5s?: number
    previsao_15s?: number
    previsao_30s?: number
    previsao_60s?: number
    candles?: any[]
    accuracy?: number
  }>
  pulsos: Array<{
    id: string
    de: string
    para: string
    energia: number
    timestamp: string
  }>
}

export interface Unit {
  id: string
  energia?: number
  state: "active" | "idle" | "charging" | "depleted"
  symbol?: string
  price?: number
  delta?: number
  tipo?: string
  previsao?: number
  previsao_5s?: number
  previsao_15s?: number
  previsao_30s?: number
  previsao_60s?: number
  candles?: any[]
  accuracy?: number
}

export interface Pulse {
  id: string
  from: string
  to: string
  energy: number
  timestamp: Date
}

function mapApiUnitState(estado: string): Unit["state"] {
  const map: Record<string, Unit["state"]> = {
    ativo: "active", ocioso: "idle", carregando: "charging", esgotado: "depleted",
    active: "active", idle: "idle", charging: "charging", depleted: "depleted"
  }
  return map[estado?.toLowerCase?.()] ?? "idle"
}

function mapApiUnit(d: ApiStatus["dados"][0]): Unit {
  return {
    id: d.id,
    energia: d.energia,
    state: mapApiUnitState(d.estado),
    symbol: d.symbol,
    price: d.price,
    delta: d.delta,
    tipo: d.tipo,
    previsao: d.previsao ?? 0,
    previsao_5s: (d as any).previsao_5s ?? 0,
    previsao_15s: (d as any).previsao_15s ?? 0,
    previsao_30s: (d as any).previsao_30s ?? 0,
    previsao_60s: (d as any).previsao_60s ?? 0,
    candles: d.candles ?? [],
    accuracy: d.accuracy,
  }
}

function mapApiPulse(p: ApiStatus["pulsos"][0]): Pulse {
  return {
    id: p.id,
    from: p.de,
    to: p.para,
    energy: p.energia,
    timestamp: new Date(p.timestamp),
  }
}

export function useApiSimulation() {
  const [mounted, setMounted] = useState(false)
  const [isRunning, setIsRunning] = useState(true)
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [units, setUnits] = useState<Unit[]>([])
  const [pulses, setPulses] = useState<Pulse[]>([])
  const [totalEnergy, setTotalEnergy] = useState(0)
  const [pollingPaused, setPollingPaused] = useState(false)

  const fetchStatus = useCallback(async () => {
    if (pollingPaused) return

    try {
      console.log("📡 Fetching status from:", `${API_BASE_URL}/status`)
      const response = await fetch(`${API_BASE_URL}/status`)
      
      if (!response.ok) throw new Error(`HTTP ${response.status}`)

      const data: ApiStatus = await response.json()
      console.log("✅ Data received:", data.dados?.length || 0, "units")

      setUnits(prevUnits => {
        const novos = data.dados.map(mapApiUnit)
        const mapa = new Map(prevUnits.map(u => [u.id, u]))
        for (const novo of novos) {
          mapa.set(novo.id, {
            ...mapa.get(novo.id),
            ...novo,
            candles: novo.candles?.length ? novo.candles : mapa.get(novo.id)?.candles
          })
        }
        return Array.from(mapa.values())
      })
      
      setPulses(data.pulsos?.slice(0, MAX_ITEMS).map(mapApiPulse) || [])
      setTotalEnergy(data.energia_total || 0)
      setIsConnected(true)
      setError(null)
      
    } catch (err) {
      console.error("❌ Fetch error:", err)
      setIsConnected(false)
      setError("Falha ao conectar com a API")
    }
  }, [pollingPaused])

  const pausePolling = useCallback(() => {
    console.log("⏸️ Polling paused")
    setPollingPaused(true)
  }, [])

  const resumePolling = useCallback(() => {
    console.log("▶️ Polling resumed")
    setPollingPaused(false)
  }, [])

  const createUnit = useCallback(async () => {
    try {
      await fetch(`${API_BASE_URL}/criar`, { method: "POST" })
      await fetchStatus()
    } catch (err) {
      console.error("Erro ao criar unidade:", err)
    }
  }, [fetchStatus])

  const sendPulse = useCallback(async () => {
    try {
      await fetch(`${API_BASE_URL}/pulso`, { method: "POST" })
      await fetchStatus()
    } catch (err) {
      console.error("Erro ao enviar pulso:", err)
    }
  }, [fetchStatus])

  const togglePause = useCallback(async () => {
    try {
      await fetch(`${API_BASE_URL}/toggle`, { method: "POST" })
      setIsRunning(prev => !prev)
    } catch (err) {
      console.error("Erro ao alternar pausa:", err)
    }
  }, [])

  const executeCommand = useCallback(async (command: string): Promise<string> => {
    try {
      const response = await fetch(`${API_BASE_URL}/comando`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ comando: command }),
      })
      if (!response.ok) return `Erro: ${response.status} ${response.statusText}`
      const data = await response.json()
      return data.prompt + " " + data.resultado || data.message || JSON.stringify(data, null, 2)
    } catch {
      return `Erro de conexão — verifique se a API está rodando em ${API_BASE_URL}`
    }
  }, [])

  const clearUnits = useCallback(() => {
    console.log("🗑️ Clearing crypto units")
    setUnits(prevUnits => prevUnits.filter(u => !u.symbol && u.tipo !== "crypto"))
  }, [])

  // INITIAL FETCH
  useEffect(() => {
    setMounted(true)
    console.log("🔧 useApiSimulation mounted, fetching initial data...")
    fetchStatus()
  }, [fetchStatus])

  // Polling interval
  useEffect(() => {
    if (!mounted) return
    if (pollingPaused) return
    
    console.log("🔄 Starting polling interval")
    const interval = setInterval(() => {
      fetchStatus()
    }, POLL_INTERVAL)
    
    return () => {
      console.log("🛑 Clearing polling interval")
      clearInterval(interval)
    }
  }, [mounted, fetchStatus, pollingPaused])

  return {
    mounted,
    isRunning,
    isConnected,
    error,
    units,
    pulses,
    totalEnergy,
    totalPulses: pulses.length,
    createUnit,
    sendPulse,
    togglePause,
    executeCommand,
    pausePolling,
    resumePolling,
    clearUnits
  }
}