"use client"
 
import { useState, useMemo } from "react"
import { Scale, Activity, Binary } from "lucide-react"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { BalanceApp } from "@/components/apps/balance-app"
import { FlowApp } from "@/components/apps/flow-app"
import { CryptoApp } from "@/components/apps/crypto-app"
import type { Unit } from "@/hooks/use-api-simulation"
 
interface Pulse {
  id: string
  from: string
  to: string
  energy: number
  timestamp: Date
}
 
interface ToolsTabProps {
  units: Unit[]
  pulses: Pulse[]
  totalEnergy: number
  executeCommand: (command: string) => Promise<string>
}
 
export function ToolsTab({ units, pulses, totalEnergy, executeCommand }: ToolsTabProps) {
  const [selectedTab, setSelectedTab] = useState("balance")
 
  // ← useMemo evita recriar array a cada render → para re-renders infinitos
  const balanceUnits = useMemo(
    () => units.map(u => ({ id: u.id, energy: u.energia ?? 0, state: undefined })),
    [units]
  )
 
  return (
    <div className="space-y-6">
      <Tabs value={selectedTab} onValueChange={setSelectedTab} className="w-full">
        <TabsList className="w-full justify-start bg-secondary/30 border border-border/50 p-1">
          <TabsTrigger
            value="balance"
            className="gap-2 data-[state=active]:bg-neon-blue/20 data-[state=active]:text-neon-blue"
          >
            <Scale className="h-4 w-4" />
            Balance
          </TabsTrigger>
          <TabsTrigger
            value="flow"
            className="gap-2 data-[state=active]:bg-neon-cyan/20 data-[state=active]:text-neon-cyan"
          >
            <Activity className="h-4 w-4" />
            Flow
          </TabsTrigger>
          <TabsTrigger
            value="crypto"
            className="gap-2 data-[state=active]:bg-amber-500/20 data-[state=active]:text-amber-400"
          >
            <Binary className="h-4 w-4" />
            Crypto
          </TabsTrigger>
        </TabsList>
 
        <TabsContent value="balance" className="mt-6">
          <div className="rounded-xl border border-border/50 bg-card/50 backdrop-blur-sm p-6">
            <BalanceApp
              units={balanceUnits}
              totalEnergy={totalEnergy}
              executeCommand={executeCommand}
            />
          </div>
        </TabsContent>
 
        <TabsContent value="flow" className="mt-6">
          <div className="rounded-xl border border-border/50 bg-card/50 backdrop-blur-sm p-6">
            <FlowApp
              pulses={pulses}
              totalEnergy={totalEnergy}
              executeCommand={executeCommand}
            />
          </div>
        </TabsContent>
 
        {/* forceMount mantém o CryptoApp montado mesmo fora da aba → gráfico não some */}
        <TabsContent value="crypto" forceMount className="mt-6">
          <div className={selectedTab === "crypto" ? "block" : "hidden"}>
            <div className="rounded-xl border border-border/50 bg-card/50 backdrop-blur-sm p-6">
              <CryptoApp
                cryptos={units}
                executeCommand={executeCommand}
              />
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}