"use client"
 
import { cn } from "@/lib/utils"
import { type LucideIcon } from "lucide-react"
 
interface SignalCardProps {
  label: string
  value: string | number
  sub?: string
  icon: LucideIcon
  trend?: "up" | "down" | "neutral"
  trendText?: string
  accent?: "green" | "red" | "blue" | "amber" | "purple"
}
 
const accentMap = {
  green: {
    icon: "text-emerald-400",
    border: "border-emerald-500/20",
    glow: "hover:shadow-[0_0_30px_rgba(16,185,129,0.12)]",
    bg: "bg-emerald-500/5",
  },
  red: {
    icon: "text-red-400",
    border: "border-red-500/20",
    glow: "hover:shadow-[0_0_30px_rgba(239,68,68,0.12)]",
    bg: "bg-red-500/5",
  },
  blue: {
    icon: "text-blue-400",
    border: "border-blue-500/20",
    glow: "hover:shadow-[0_0_30px_rgba(59,130,246,0.12)]",
    bg: "bg-blue-500/5",
  },
  amber: {
    icon: "text-amber-400",
    border: "border-amber-500/20",
    glow: "hover:shadow-[0_0_30px_rgba(245,158,11,0.12)]",
    bg: "bg-amber-500/5",
  },
  purple: {
    icon: "text-purple-400",
    border: "border-purple-500/20",
    glow: "hover:shadow-[0_0_30px_rgba(168,85,247,0.12)]",
    bg: "bg-purple-500/5",
  },
}
 
const trendMap = {
  up: { color: "text-emerald-400", symbol: "↑" },
  down: { color: "text-red-400", symbol: "↓" },
  neutral: { color: "text-muted-foreground", symbol: "→" },
}
 
export function SignalCard({
  label,
  value,
  sub,
  icon: Icon,
  trend,
  trendText,
  accent = "blue",
}: SignalCardProps) {
  const a = accentMap[accent]
  const t = trend ? trendMap[trend] : null
 
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-xl border bg-card/60 backdrop-blur-sm p-5 transition-all duration-300",
        a.border,
        a.glow
      )}
    >
      <div className={cn("absolute inset-0 opacity-40", a.bg)} />
      <div className="relative flex items-start justify-between">
        <div className="space-y-1.5">
          <p className="text-xs font-medium text-muted-foreground tracking-wide uppercase">
            {label}
          </p>
          <p className="text-2xl font-semibold tracking-tight text-foreground leading-none">
            {typeof value === "number" ? value.toLocaleString() : value}
          </p>
          {sub && (
            <p className="text-xs text-muted-foreground">{sub}</p>
          )}
          {t && trendText && (
            <p className={cn("text-xs font-medium flex items-center gap-1", t.color)}>
              <span>{t.symbol}</span>
              <span>{trendText}</span>
            </p>
          )}
        </div>
        <div className={cn("flex h-9 w-9 items-center justify-center rounded-lg bg-secondary/60", a.icon)}>
          <Icon className="h-4 w-4" />
        </div>
      </div>
    </div>
  )
}