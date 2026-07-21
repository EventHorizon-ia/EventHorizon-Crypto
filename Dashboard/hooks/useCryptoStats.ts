// hooks/useCryptoStats.ts
import { useState, useEffect, useCallback } from "react"
import { API_BASE_URL } from '@/lib/api';
interface CoinPerformance {
  symbol: string
  acertos: number
  erros: number
  total: number
  acuracia: number
}

interface HorarioPerformance {
  hora: string
  total: number
  acertos: number
  acuracia: number
}

interface StatsData {
  acuracia_geral: number
  total_previsoes: number
  acertos: number
  melhores_horarios: HorarioPerformance[]
  piores_horarios: HorarioPerformance[]
  performance_moedas: CoinPerformance[]
  evolucao: any[]
  sinais_atuais: any[]
}

export function useCryptoStats() {
  const [stats, setStats] = useState<StatsData>({
    acuracia_geral: 0,
    total_previsoes: 0,
    acertos: 0,
    melhores_horarios: [],
    piores_horarios: [],
    performance_moedas: [],
    evolucao: [],
    sinais_atuais: []
  })
  const [loading, setLoading] = useState(true)

  const fetchStats = useCallback(async () => {
    try {
      setLoading(true)
      
      // ⭐ Busca do endpoint /trader/stats
      const response = await fetch(`${API_BASE_URL}/trader/stats`)
      const data = await response.json()
      
      if (data) {
        setStats({
          acuracia_geral: data.acuracia_geral || 0,
          total_previsoes: data.total_previsoes || 0,
          acertos: data.total_acertos || 0,
          melhores_horarios: data.melhores_horarios || [],
          piores_horarios: data.piores_horarios || [],
          performance_moedas: (data.performance_moedas || []).map((coin: any) => ({
            symbol: coin.symbol,
            acertos: coin.acertos,
            erros: coin.erros,
            total: coin.total,
            acuracia: coin.acuracia
          })),
          evolucao: data.evolucao || [],
          sinais_atuais: data.sinais_atuais || []
        })
      }
    } catch (error) {
      console.error("Erro ao buscar stats do trader:", error)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchStats()
    // Atualiza a cada 10 segundos
    const interval = setInterval(fetchStats, 10000)
    return () => clearInterval(interval)
  }, [fetchStats])

  return { stats, loading, refresh: fetchStats }
}