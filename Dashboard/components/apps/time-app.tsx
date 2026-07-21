"use client"

import { Clock, CalendarDays, Timer } from "lucide-react"
import { AppCard } from "./app-card"
import { useState, useEffect } from "react"

interface TimeAppProps {
  startTime?: Date
}

export function TimeApp({ startTime }: TimeAppProps) {
  const [currentTime, setCurrentTime] = useState(new Date())
  const [elapsedTime, setElapsedTime] = useState("00:00:00")

  useEffect(() => {
    const interval = setInterval(() => {
      const now = new Date()
      setCurrentTime(now)
      
      if (startTime) {
        const elapsed = Math.floor((now.getTime() - startTime.getTime()) / 1000)
        const hours = Math.floor(elapsed / 3600)
        const minutes = Math.floor((elapsed % 3600) / 60)
        const seconds = elapsed % 60
        setElapsedTime(
          `${hours.toString().padStart(2, "0")}:${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`
        )
      }
    }, 1000)

    return () => clearInterval(interval)
  }, [startTime])

  return (
    <AppCard
      title="Tempo"
      description="Cronômetro da simulação"
      icon={Clock}
      variant="cyan"
    >
      <div className="space-y-4">
        <div className="text-center p-4 rounded-lg bg-secondary/30">
          <p className="text-xs text-muted-foreground mb-2">Hora Atual</p>
          <p className="text-3xl font-mono font-bold text-foreground">
            {currentTime.toLocaleTimeString("pt-BR")}
          </p>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="flex items-center gap-3 p-3 rounded-lg bg-secondary/30">
            <CalendarDays className="h-5 w-5 text-neon-blue" />
            <div>
              <p className="text-xs text-muted-foreground">Data</p>
              <p className="text-sm font-semibold text-foreground">
                {currentTime.toLocaleDateString("pt-BR")}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 p-3 rounded-lg bg-secondary/30">
            <Timer className="h-5 w-5 text-neon-purple" />
            <div>
              <p className="text-xs text-muted-foreground">Ativo há</p>
              <p className="text-sm font-mono font-semibold text-neon-cyan">
                {elapsedTime}
              </p>
            </div>
          </div>
        </div>
      </div>
    </AppCard>
  )
}
