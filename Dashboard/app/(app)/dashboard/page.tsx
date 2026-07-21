"use client"

import { useState, useMemo, useCallback } from "react"
import { LayoutDashboard, Wifi, WifiOff, TrendingUp } from "lucide-react"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { DashboardTab } from "@/components/tabs/dashboard-tab"
import { CryptoApp } from "@/components/apps/crypto-app"
import { useApiSimulation } from "@/hooks/use-api-simulation"
import { cn } from "@/lib/utils"
import { ChatBot } from "@/components/apps/ChatBot"

export default function UniverseOS() {
  const {
    mounted,
    isRunning,
    isConnected,
    error,
    units,
    pulses,
    totalEnergy,
    totalPulses,
    createUnit,
    sendPulse,
    togglePause,
    executeCommand,
    pausePolling,
    resumePolling,
    clearUnits
  } = useApiSimulation()

  // ⭐ Estado para forçar re-render do CryptoApp
  const [refreshKey, setRefreshKey] = useState(0)
  const [removedSymbols, setRemovedSymbols] = useState<Set<string>>(new Set())

  const connectionStatus = useMemo(() => {
    if (isConnected) {
      return {
        icon: Wifi,
        text: "API Conectada",
        className: "text-green-400 border-green-500/30 bg-green-500/10"
      }
    }
    return {
      icon: WifiOff,
      text: error || "Desconectado",
      className: "text-red-400 border-red-500/30 bg-red-500/10"
    }
  }, [isConnected, error])

  // Filtra apenas unidades crypto
  const cryptoUnits = useMemo(() => {
    return units.filter(u => 
      (u.symbol || u.tipo === "crypto") && 
      !removedSymbols.has(u.symbol ?? "")
    )
  }, [units, removedSymbols])

  // ⭐ Função para forçar refresh dos dados
  const handleRefresh = useCallback(async () => {
    setRefreshKey(prev => prev + 1)
    try {
      if (executeCommand) {
        await executeCommand("refresh")
      }
    } catch (error) {
      console.error("Refresh error:", error)
    }
  }, [executeCommand])

  // ⭐ Função chamada quando moedas são removidas
  const handleCoinsRemoved = useCallback((symbols: string[]) => {
    setRemovedSymbols(prev => {
      const next = new Set(prev)
      symbols.forEach(s => next.add(s))
      return next
    })
    if (clearUnits && typeof clearUnits === 'function') {
      clearUnits()
    }
  }, [clearUnits])

  if (!mounted) {
    return (
      <main className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-neon-blue/30 border-t-neon-blue" />
          <p className="text-muted-foreground text-sm">Conectando ao servidor...</p>
        </div>
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-background">
      {/* Background gradient effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-neon-blue/5 rounded-full blur-[150px]" />
        <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] bg-neon-purple/5 rounded-full blur-[150px]" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-neon-cyan/3 rounded-full blur-[200px]" />
      </div>

      <div className="relative z-10 container mx-auto px-4 py-6">
        {/* Header */}
        <header className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-neon-blue to-neon-cyan/80">
                <TrendingUp className="h-5 w-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-neon-blue to-neon-cyan bg-clip-text text-transparent">
                  TRADER AI
                </h1>
                <p className="text-xs text-muted-foreground">Sistema de Trading com IA Adaptativa</p>
              </div>
            </div>

            {/* Connection Status */}
            <div className={cn(
              "flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-medium",
              connectionStatus.className
            )}>
              <connectionStatus.icon className="h-3.5 w-3.5" />
              <span>{connectionStatus.text}</span>
            </div>
          </div>
        </header>

        {/* Apenas 2 abas: Dashboard e Crypto */}
        <Tabs defaultValue="dashboard" className="w-full">
          <TabsList className="mb-6 bg-secondary/50 border border-border/50 p-1">
            <TabsTrigger 
              value="dashboard" 
              className="gap-2 data-[state=active]:bg-neon-blue/20 data-[state=active]:text-neon-blue data-[state=active]:border-neon-blue/30"
            >
              <LayoutDashboard className="h-4 w-4" />
              Dashboard
            </TabsTrigger>
            <TabsTrigger 
              value="crypto"
              className="gap-2 data-[state=active]:bg-gradient-to-r data-[state=active]:from-neon-blue/20 data-[state=active]:to-neon-cyan/20 data-[state=active]:text-neon-cyan data-[state=active]:border-neon-cyan/30"
            >
              <TrendingUp className="h-4 w-4" />
              Crypto Trading
            </TabsTrigger>
          </TabsList>

          <TabsContent value="dashboard" className="mt-0">
            <DashboardTab
            />
          </TabsContent>

          <TabsContent value="crypto" className="mt-0">
            <CryptoApp
              key={`crypto-app-${refreshKey}`}
              cryptos={cryptoUnits}
              executeCommand={executeCommand}
              onRefresh={handleRefresh}
              onCoinsRemoved={handleCoinsRemoved}
              pausePolling={pausePolling}
              resumePolling={resumePolling}
              clearUnits={clearUnits}
            />
          </TabsContent>
        </Tabs>

        {/* Footer */}
        <footer className="text-center text-xs text-muted-foreground py-4 mt-6 border-t border-border/30">
          <p>TRADER AI • Sistema de Trading com Inteligência Adaptativa</p>
        </footer>
        <ChatBot />
      </div>
    </main>
  )
}