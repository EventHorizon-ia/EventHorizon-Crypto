"use client"

import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { Pause, Play, Plus, Send, Settings } from "lucide-react"

interface ControlPanelProps {
  isRunning: boolean
  onCreateUnit: () => void
  onSendPulse: () => void
  onTogglePause: () => void
}

export function ControlPanel({ isRunning, onCreateUnit, onSendPulse, onTogglePause }: ControlPanelProps) {
  return (
    <div className="rounded-xl border border-border/50 bg-card/50 backdrop-blur-sm p-4 shadow-lg">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
          <Settings className="h-4 w-4 text-muted-foreground" />
          Controles
        </h3>
        <div className={cn(
          "flex items-center gap-2 text-xs font-medium px-2 py-1 rounded-full",
          isRunning 
            ? "bg-green-500/10 text-green-400 border border-green-500/20" 
            : "bg-yellow-500/10 text-yellow-400 border border-yellow-500/20"
        )}>
          <span className={cn(
            "h-1.5 w-1.5 rounded-full",
            isRunning ? "bg-green-400 animate-pulse" : "bg-yellow-400"
          )} />
          {isRunning ? "Executando" : "Pausado"}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <Button
          onClick={onCreateUnit}
          className="bg-neon-blue/20 hover:bg-neon-blue/30 text-neon-blue border border-neon-blue/30 transition-all duration-200 hover:shadow-[0_0_20px_rgba(59,130,246,0.3)]"
          variant="outline"
        >
          <Plus className="h-4 w-4 mr-2" />
          Nova Unidade
        </Button>

        <Button
          onClick={onSendPulse}
          className="bg-neon-cyan/20 hover:bg-neon-cyan/30 text-neon-cyan border border-neon-cyan/30 transition-all duration-200 hover:shadow-[0_0_20px_rgba(0,230,230,0.3)]"
          variant="outline"
        >
          <Send className="h-4 w-4 mr-2" />
          Enviar Pulso
        </Button>

        <Button
          onClick={onTogglePause}
          className={cn(
            "transition-all duration-200",
            isRunning
              ? "bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-400 border border-yellow-500/30 hover:shadow-[0_0_20px_rgba(234,179,8,0.3)]"
              : "bg-green-500/20 hover:bg-green-500/30 text-green-400 border border-green-500/30 hover:shadow-[0_0_20px_rgba(34,197,94,0.3)]"
          )}
          variant="outline"
        >
          {isRunning ? (
            <>
              <Pause className="h-4 w-4 mr-2" />
              Pausar
            </>
          ) : (
            <>
              <Play className="h-4 w-4 mr-2" />
              Retomar
            </>
          )}
        </Button>
      </div>
    </div>
  )
}
