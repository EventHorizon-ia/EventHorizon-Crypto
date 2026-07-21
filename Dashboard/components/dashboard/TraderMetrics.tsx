// components/dashboard/TraderMetrics.tsx (NOVO componente)
"use client"
import { cn } from "@/lib/utils"
import { TrendingUp, TrendingDown, Zap, Clock } from "lucide-react"

interface TraderMetricsProps {
  accuracy: number
  bestTime: string
  worstTime: string
  totalTrades: number
  winRate: number
}

export function TraderMetrics({ accuracy, bestTime, worstTime, totalTrades, winRate }: TraderMetricsProps) {
  return (
    <div className="rounded-xl border border-border/50 bg-card/50 backdrop-blur-sm p-5 space-y-4">
      <h3 className="text-sm font-semibold flex items-center gap-2">
        <Zap className="h-4 w-4 text-yellow-500" />
        MÉTRICAS DA IA
      </h3>
      
      <div className="space-y-3">
        <div className="flex justify-between items-center">
          <span className="text-xs text-muted-foreground">Acurácia Geral</span>
          <span className={cn(
            "text-lg font-bold",
            accuracy >= 55 ? "text-green-400" : accuracy >= 45 ? "text-yellow-400" : "text-red-400"
          )}>
            {accuracy}%
          </span>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-xs text-muted-foreground">Taxa de Acertos</span>
          <span className="text-lg font-bold text-green-400">{winRate}%</span>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-xs text-muted-foreground">Total de Trades</span>
          <span className="text-lg font-bold text-foreground">{totalTrades}</span>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-xs text-muted-foreground">Melhor Horário</span>
          <span className="text-sm font-mono text-green-400">{bestTime}</span>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-xs text-muted-foreground">Pior Horário</span>
          <span className="text-sm font-mono text-red-400">{worstTime}</span>
        </div>
      </div>
    </div>
  )
}