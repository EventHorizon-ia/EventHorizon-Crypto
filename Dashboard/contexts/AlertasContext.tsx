// contexts/AlertasContext.tsx
"use client"

import { createContext, useContext, useState, useEffect, useCallback } from "react"
import { API_BASE_URL } from "@/lib/api"

interface Alerta {
  id: string
  tipo: string
  moeda: string
  direcao: string
  horizonte: string
  previsao: number
  confianca: number
  mensagem: string
  timestamp: number
  lido: boolean
}

interface AlertasContextType {
  alertas: Alerta[]
  alertasNaoLidos: number
  verificarAlertas: () => Promise<void>
  marcarLido: (id: string) => void
  ultimoAlerta: Alerta | null
  testarAlerta: () => void  // ⭐ ADICIONE ESTA LINHA
}

const AlertasContext = createContext<AlertasContextType>({
  alertas: [],
  alertasNaoLidos: 0,
  verificarAlertas: async () => {},
  marcarLido: () => {},
  ultimoAlerta: null,
  testarAlerta: () => {}  // ⭐ ADICIONE ESTA LINHA
})

export function AlertasProvider({ children }: { children: React.ReactNode }) {
  const [alertas, setAlertas] = useState<Alerta[]>([])
  const [ultimoAlerta, setUltimoAlerta] = useState<Alerta | null>(null)

  const alertasNaoLidos = alertas.filter(a => !a.lido).length

  const verificarAlertas = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/alertas/verificar`)
      const data = await res.json()
      
      if (data.alertas && data.alertas.length > 0) {
        const novosAlertas: Alerta[] = data.alertas.map((a: any) => ({
          ...a,
          id: `${a.moeda}-${a.horizonte}-${a.timestamp}`,
          lido: false
        }))
        
        setAlertas(prev => {
          // Evita duplicados
          const idsExistentes = new Set(prev.map(a => a.id))
          const realmenteNovos = novosAlertas.filter(a => !idsExistentes.has(a.id))
          return [...realmenteNovos, ...prev].slice(0, 50)
        })
        
        if (novosAlertas.length > 0) {
          setUltimoAlerta(novosAlertas[0])
          // Auto-limpa o último alerta após 5 segundos
          setTimeout(() => setUltimoAlerta(null), 5000)
        }
      }
    } catch (e) {
      console.error("Erro ao verificar alertas:", e)
    }
  }, [])

  const marcarLido = useCallback((id: string) => {
    setAlertas(prev => prev.map(a => a.id === id ? { ...a, lido: true } : a))
  }, [])

  // Verifica alertas a cada 30 segundos
  useEffect(() => {
    verificarAlertas()
    const interval = setInterval(verificarAlertas, 30000)
    return () => clearInterval(interval)
  }, [verificarAlertas])

  // contexts/AlertasContext.tsx
// Adicione esta função dentro do AlertasProvider:

const testarAlerta = useCallback(() => {
  const alertaTeste: Alerta = {
    id: `teste-${Date.now()}`,
    tipo: "sinal",
    moeda: "BTC",
    direcao: "COMPRAR",
    horizonte: "5min",
    previsao: 8.5,
    confianca: 67,
    mensagem: "COMPRAR BTC - 5min - Conf: 67%",
    timestamp: Date.now() / 1000,
    lido: false
  }
  
  setAlertas(prev => [alertaTeste, ...prev])
  setUltimoAlerta(alertaTeste)
  setTimeout(() => setUltimoAlerta(null), 5000)
}, [])

// Adicione no return do value:
return (
  <AlertasContext.Provider value={{ 
    alertas, alertasNaoLidos, verificarAlertas, marcarLido, ultimoAlerta,
    testarAlerta  // ⭐ EXPORTA
  }}>
    {children}
  </AlertasContext.Provider>
)
}

export const useAlertas = () => useContext(AlertasContext)