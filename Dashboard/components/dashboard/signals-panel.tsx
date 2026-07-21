"use client"
 
import { cn } from "@/lib/utils"
import { TrendingUp, TrendingDown, Minus } from "lucide-react"
 
export interface SignalUnit {
  id: string
  symbol?: string
  price?: number
  delta?: number
  energia?: number
  previsao?: number
  tipo?: string
}
 
interface SignalsPanelProps {
  units: SignalUnit[]
}
 
function getSignal(previsao: number): {
  label: string
  color: string
  bg: string
  icon: typeof TrendingUp
} {
  if (previsao > 2) return { label: "Compra forte", color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20", icon: TrendingUp }
  if (previsao > 0.5) return { label: "Compra", color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20", icon: TrendingUp }
  if (previsao < -2) return { label: "Venda forte", color: "text-red-400", bg: "bg-red-500/10 border-red-500/20", icon: TrendingDown }
  if (previsao < -0.5) return { label: "Venda", color: "text-red-400", bg: "bg-red-500/10 border-red-500/20", icon: TrendingDown }
  return { label: "Neutro", color: "text-muted-foreground", bg: "bg-secondary/40 border-border/30", icon: Minus }
}
 
function getConfidence(energia: number): number {
  return Math.round(Math.min(100, Math.max(0, energia * 10)))
}
 
export function SignalsPanel({ units }: SignalsPanelProps) {
  const cryptos = units.filter(u => u.tipo === "crypto" && u.symbol)
 
  return (
    <div className="rounded-xl border border-border/50 bg-card/50 backdrop-blur-sm p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-foreground">Sinais ativos</h3>
        <div className="flex items-center gap-1.5">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-400" />
          </span>
          <span className="text-xs text-muted-foreground">Ao vivo</span>
        </div>
      </div>
 
      {/* Header */}
      <div className="grid grid-cols-4 gap-2 text-[10px] font-medium text-muted-foreground uppercase tracking-wider pb-2 border-b border-border/30 mb-1">
        <span>Ativo</span>
        <span className="text-right">Preço</span>
        <span className="text-right">Confiança</span>
        <span className="text-right">Sinal</span>
      </div>
 
      <div className="space-y-0.5 max-h-[280px] overflow-y-auto">
        {cryptos.length === 0 ? (
          <p className="text-xs text-muted-foreground text-center py-8">
            Nenhum sinal disponível — inicie o Crypto App
          </p>
        ) : (
          cryptos.map((unit) => {
            const previsao = unit.previsao ?? 0
            const energia = unit.energia ?? 0
            const signal = getSignal(previsao)
            const confidence = getConfidence(energia)
            const delta = unit.delta ?? 0
            const SignalIcon = signal.icon
 
            return (
              <div
                key={unit.id}
                className="grid grid-cols-4 gap-2 items-center py-2 px-2 rounded-lg hover:bg-secondary/30 transition-colors"
              >
                {/* Nome */}
                <div>
                  <p className="text-sm font-medium text-foreground font-mono">
                    {unit.symbol?.replace("USDT", "")}
                  </p>
                  <p className={cn(
                    "text-[10px] flex items-center gap-0.5",
                    delta > 0 ? "text-emerald-400" : delta < 0 ? "text-red-400" : "text-muted-foreground"
                  )}>
                    {delta > 0 ? "+" : ""}{delta.toFixed(2)}
                  </p>
                </div>
 
                {/* Preço */}
                <p className="text-sm font-mono text-right text-foreground">
                  ${unit.price?.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) ?? "—"}
                </p>
 
                {/* Confiança */}
                <div className="flex flex-col items-end gap-1">
                  <span className="text-xs text-muted-foreground">{confidence}%</span>
                  <div className="w-full max-w-[60px] h-1 bg-secondary rounded-full overflow-hidden">
                    <div
                      className={cn(
                        "h-full rounded-full transition-all duration-500",
                        confidence > 70 ? "bg-emerald-500" :
                        confidence > 40 ? "bg-amber-500" : "bg-red-500"
                      )}
                      style={{ width: `${confidence}%` }}
                    />
                  </div>
                </div>
 
                {/* Sinal */}
                <div className="flex justify-end">
                  <span className={cn(
                    "inline-flex items-center gap-1 text-[10px] font-medium px-2 py-1 rounded-full border",
                    signal.bg,
                    signal.color
                  )}>
                    <SignalIcon className="h-2.5 w-2.5" />
                    {signal.label}
                  </span>
                </div>
              </div>
            )
          })
        )}
      </div>
 
      {cryptos.length > 0 && (
        <div className="mt-3 pt-3 border-t border-border/30 flex justify-between text-[10px] text-muted-foreground">
          <span>{cryptos.length} ativos monitorados</span>
          <span>Atualizado agora</span>
        </div>
      )}
    </div>
  )
}