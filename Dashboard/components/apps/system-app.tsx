"use client"

import { Server, Cpu, HardDrive, Wifi } from "lucide-react"
import { AppCard } from "./app-card"
import { cn } from "@/lib/utils"

interface SystemAppProps {
  isConnected: boolean
  isRunning: boolean
  totalUnits: number
  totalEnergy: number
  onTogglePause: () => void
}

export function SystemApp({ isConnected, isRunning, totalUnits, totalEnergy, onTogglePause }: SystemAppProps) {
  return (
    <AppCard
      title="Sistema"
      description="Status e controle do núcleo"
      icon={Server}
      variant="cyan"
      actions={[
        {
          label: isRunning ? "Pausar Sistema" : "Retomar Sistema",
          onClick: onTogglePause,
          variant: isRunning ? "purple" : "cyan"
        }
      ]}
    >
      <div className="grid grid-cols-2 gap-4">
        <div className="flex items-center gap-3 p-3 rounded-lg bg-secondary/30">
          <Wifi className={cn(
            "h-5 w-5",
            isConnected ? "text-green-400" : "text-red-400"
          )} />
          <div>
            <p className="text-xs text-muted-foreground">Conexão</p>
            <p className={cn(
              "text-sm font-semibold",
              isConnected ? "text-green-400" : "text-red-400"
            )}>
              {isConnected ? "Online" : "Offline"}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 p-3 rounded-lg bg-secondary/30">
          <Cpu className={cn(
            "h-5 w-5",
            isRunning ? "text-neon-cyan" : "text-yellow-400"
          )} />
          <div>
            <p className="text-xs text-muted-foreground">Estado</p>
            <p className={cn(
              "text-sm font-semibold",
              isRunning ? "text-neon-cyan" : "text-yellow-400"
            )}>
              {isRunning ? "Executando" : "Pausado"}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 p-3 rounded-lg bg-secondary/30">
          <Server className="h-5 w-5 text-neon-blue" />
          <div>
            <p className="text-xs text-muted-foreground">Unidades</p>
            <p className="text-sm font-semibold text-foreground">{totalUnits}</p>
          </div>
        </div>

        <div className="flex items-center gap-3 p-3 rounded-lg bg-secondary/30">
          <HardDrive className="h-5 w-5 text-neon-purple" />
          <div>
            <p className="text-xs text-muted-foreground">Energia</p>
            <p className="text-sm font-semibold text-foreground">{totalEnergy.toLocaleString()}</p>
          </div>
        </div>
      </div>
    </AppCard>
  )
}
