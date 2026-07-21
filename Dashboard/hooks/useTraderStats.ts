// hooks/useTraderStats.ts
"use client"

import { useState, useEffect } from "react"
import { API_BASE_URL } from '@/lib/api';
interface TraderStats {
  acuracia_geral: number
  total_previsoes: number
  total_acertos: number
  performance_moedas: Array<{
    symbol: string
    total: number
    acertos: number
    acuracia: number
  }>
  melhores_horarios: Array<{
    hora: string
    total: number
    acuracia: number
  }>
  piores_horarios: Array<{
    hora: string
    total: number
    acuracia: number
  }>
  evolucao: Array<{
    data: string
    total: number
    acuracia: number
  }>
  sinais_atuais: Array<{
    symbol: string
    previsao: number
    confianca: number
    acertos: number
    erros: number
  }>
}

export function useTraderStats() {
  const [stats, setStats] = useState<TraderStats>({
    acuracia_geral: 0,
    total_previsoes: 0,
    total_acertos: 0,
    performance_moedas: [],
    melhores_horarios: [],
    piores_horarios: [],
    evolucao: [],
    sinais_atuais: []
  })
  const [loading, setLoading] = useState(true)

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/trader/stats`)
      const data = await response.json()
      setStats(data)
    } catch (error) {
      console.error("Erro ao buscar estatisticas:", error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStats()
    const interval = setInterval(fetchStats, 30000)
    return () => clearInterval(interval)
  }, [])

  return { stats, loading, refetch: fetchStats }
}