"use client"

import { SystemApp } from "@/components/apps/system-app"
import { DataApp } from "@/components/apps/data-app"
import { PulseApp } from "@/components/apps/pulse-app"
import { TimeApp } from "@/components/apps/time-app"
import { BalanceApp } from "@/components/apps/balance-app"
import type { Unit } from "@/components/dashboard/units-panel"
import type { Pulse } from "@/components/dashboard/pulses-panel"

interface AppsTabProps {
  isConnected: boolean
  isRunning: boolean
  units: Unit[]
  pulses: Pulse[]
  totalEnergy: number
  startTime: Date
  onTogglePause: () => void
  onCreateUnit: () => void
  onSendPulse: () => void
}

export function AppsTab({
  isConnected,
  isRunning,
  units,
  pulses,
  totalEnergy,
  startTime,
  onTogglePause,
  onCreateUnit,
  onSendPulse
}: AppsTabProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

      <SystemApp
        isConnected={isConnected}
        isRunning={isRunning}
        totalUnits={units.length}
        totalEnergy={totalEnergy}
        onTogglePause={onTogglePause}
      />

      <DataApp
        units={units}
        onCreateUnit={onCreateUnit}
      />

      <PulseApp
        pulses={pulses}
        onSendPulse={onSendPulse}
      />

      <TimeApp startTime={startTime} />


    </div>
  )
}