"use client"
 
import { cn } from "@/lib/utils"
import { ArrowRight, Zap, CheckCircle, AlertTriangle, GitMerge } from "lucide-react"
 
export interface ActivityEvent {
  id: string
  type: "pulse" | "balance" | "flow" | "alert" | "loop"
  from?: string
  to?: string
  energy?: number
  message?: string
  timestamp: Date
}
 
interface ActivityFeedProps {
  pulses: Array<{
    id: string
    from: string
    to: string
    energy: number
    timestamp: Date
  }>
  systemEvents?: ActivityEvent[]
}
 
function getRelativeTime(date: Date) {
  const s = Math.floor((Date.now() - date.getTime()) / 1000)
  if (s < 5) return "agora"
  if (s < 60) return `${s}s`
  return `${Math.floor(s / 60)}m`
}
 
const eventConfig = {
  pulse: { icon: Zap, color: "text-blue-400", dot: "bg-blue-400" },
  balance: { icon: CheckCircle, color: "text-emerald-400", dot: "bg-emerald-400" },
  flow: { icon: GitMerge, color: "text-purple-400", dot: "bg-purple-400" },
  alert: { icon: AlertTriangle, color: "text-amber-400", dot: "bg-amber-400" },
  loop: { icon: GitMerge, color: "text-cyan-400", dot: "bg-cyan-400" },
}
 
export function ActivityFeed({ pulses, systemEvents = [] }: ActivityFeedProps) {
  // Converte pulsos em eventos
  const pulseEvents: ActivityEvent[] = pulses.slice(0, 15).map(p => ({
    id: p.id,
    type: "pulse",
    from: p.from,
    to: p.to,
    energy: p.energy,
    timestamp: p.timestamp,
  }))
 
  // Combina e ordena
  const allEvents = [...systemEvents, ...pulseEvents]
    .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
    .slice(0, 18)
 
  return (
    <div className="rounded-xl border border-border/50 bg-card/50 backdrop-blur-sm p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-foreground">Atividade</h3>
        <span className="text-xs text-muted-foreground">{allEvents.length} eventos</span>
      </div>
 
      <div className="space-y-0 max-h-[280px] overflow-y-auto">
        {allEvents.length === 0 ? (
          <p className="text-xs text-muted-foreground text-center py-8">
            Aguardando atividade do sistema...
          </p>
        ) : (
          allEvents.map((event, i) => {
            const cfg = eventConfig[event.type]
            const EventIcon = cfg.icon
 
            return (
              <div
                key={event.id}
                className={cn(
                  "flex items-center gap-3 py-2 px-2 rounded-lg transition-colors",
                  i === 0 ? "bg-secondary/20" : "hover:bg-secondary/20"
                )}
              >
                <div className={cn("w-1.5 h-1.5 rounded-full flex-shrink-0", cfg.dot)} />
 
                <div className="flex-1 min-w-0">
                  {event.type === "pulse" ? (
                    <div className="flex items-center gap-1.5 text-xs text-muted-foreground font-mono">
                      <span className="text-foreground">{event.from}</span>
                      <ArrowRight className="h-2.5 w-2.5 flex-shrink-0" />
                      <span className="text-foreground">{event.to}</span>
                      {event.energy !== undefined && (
                        <span className={cn("ml-auto flex-shrink-0", cfg.color)}>
                          +{event.energy.toFixed(2)}
                        </span>
                      )}
                    </div>
                  ) : (
                    <p className="text-xs text-muted-foreground truncate">
                      {event.message}
                    </p>
                  )}
                </div>
 
                <span className="text-[10px] text-muted-foreground flex-shrink-0 w-8 text-right">
                  {getRelativeTime(event.timestamp)}
                </span>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}