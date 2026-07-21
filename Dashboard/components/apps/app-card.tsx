"use client"

import { cn } from "@/lib/utils"
import { type LucideIcon } from "lucide-react"
import { Button } from "@/components/ui/button"

interface AppAction {
  label: string
  onClick: () => void
  variant?: "cyan" | "blue" | "purple"
  disabled?: boolean
}

interface AppCardProps {
  title: string
  description: string
  icon: LucideIcon
  variant?: "cyan" | "blue" | "purple"
  children?: React.ReactNode
  actions?: AppAction[]
}

const variantStyles = {
  cyan: {
    border: "border-neon-cyan/20",
    shadow: "shadow-[0_0_30px_rgba(0,230,230,0.1)]",
    icon: "text-neon-cyan",
    glow: "bg-neon-cyan"
  },
  blue: {
    border: "border-neon-blue/20",
    shadow: "shadow-[0_0_30px_rgba(59,130,246,0.1)]",
    icon: "text-neon-blue",
    glow: "bg-neon-blue"
  },
  purple: {
    border: "border-neon-purple/20",
    shadow: "shadow-[0_0_30px_rgba(147,51,234,0.1)]",
    icon: "text-neon-purple",
    glow: "bg-neon-purple"
  }
}

const buttonStyles = {
  cyan: "bg-neon-cyan/20 hover:bg-neon-cyan/30 text-neon-cyan border-neon-cyan/30 hover:shadow-[0_0_20px_rgba(0,230,230,0.3)]",
  blue: "bg-neon-blue/20 hover:bg-neon-blue/30 text-neon-blue border-neon-blue/30 hover:shadow-[0_0_20px_rgba(59,130,246,0.3)]",
  purple: "bg-neon-purple/20 hover:bg-neon-purple/30 text-neon-purple border-neon-purple/30 hover:shadow-[0_0_20px_rgba(147,51,234,0.3)]"
}

export function AppCard({ title, description, icon: Icon, variant = "blue", children, actions }: AppCardProps) {
  const styles = variantStyles[variant]

  return (
    <div className={cn(
      "relative overflow-hidden rounded-xl border bg-card/50 backdrop-blur-sm p-6 transition-all duration-300",
      styles.border,
      styles.shadow
    )}>
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={cn(
            "flex h-10 w-10 items-center justify-center rounded-lg bg-secondary/50",
            styles.icon
          )}>
            <Icon className="h-5 w-5" />
          </div>
          <div>
            <h3 className="font-semibold text-foreground">{title}</h3>
            <p className="text-xs text-muted-foreground">{description}</p>
          </div>
        </div>
      </div>

      {/* Content */}
      {children && (
        <div className="mb-4">
          {children}
        </div>
      )}

      {/* Actions */}
      {actions && actions.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {actions.map((action, index) => (
            <Button
              key={index}
              onClick={action.onClick}
              disabled={action.disabled}
              variant="outline"
              size="sm"
              className={cn(
                "transition-all duration-200",
                buttonStyles[action.variant || variant]
              )}
            >
              {action.label}
            </Button>
          ))}
        </div>
      )}

      {/* Glow effect */}
      <div className={cn(
        "absolute -bottom-2 -right-2 h-20 w-20 rounded-full blur-3xl opacity-10",
        styles.glow
      )} />
    </div>
  )
}
