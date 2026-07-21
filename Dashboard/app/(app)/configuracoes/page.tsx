"use client"

import { useState, useEffect } from "react"
import {
  Settings, Sun, Moon, Clock, BarChart3,
  Coins, Save, RotateCcw, Check
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

// ============================================
// TIPOS
// ============================================

interface Configs {
  tema: "escuro" | "claro"
  frequenciaAtualizacao: number  // segundos
  graficoTipo: "candlestick" | "line" | "area"
  moedaPadrao: string
  timeframePadrao: number
}

const CONFIG_PADRAO: Configs = {
  tema: "escuro",
  frequenciaAtualizacao: 5,
  graficoTipo: "candlestick",
  moedaPadrao: "BTCUSDT",
  timeframePadrao: 5
}

const STORAGE_KEY = "trader_config"

// ============================================
// COMPONENTE
// ============================================

export default function ConfiguracoesPage() {
  const [config, setConfig] = useState<Configs>(CONFIG_PADRAO)
  const [salvo, setSalvo] = useState(false)

  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      try {
        setConfig({ ...CONFIG_PADRAO, ...JSON.parse(saved) })
      } catch {}
    }
  }, [])

  function atualizar(chave: keyof Configs, valor: any) {
    setConfig(prev => ({ ...prev, [chave]: valor }))
    setSalvo(false)
  }

  function salvar() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(config))
    setSalvo(true)
    setTimeout(() => setSalvo(false), 2000)
    
    // Aplica o tema imediatamente
    document.documentElement.classList.toggle("light", config.tema === "claro")
  }

  function restaurar() {
    setConfig(CONFIG_PADRAO)
    localStorage.removeItem(STORAGE_KEY)
    setSalvo(true)
    setTimeout(() => setSalvo(false), 2000)
  }

  return (
    <div className="p-6 space-y-6 max-w-2xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Configurações</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Personalize sua experiência de trading
        </p>
      </div>

      {/* Tema */}
      <div className="rounded-xl border border-border/50 bg-secondary/10 p-5">
        <h3 className="text-sm font-bold mb-4 flex items-center gap-2">
          <Settings className="w-4 h-4 text-cyan-400" />
          Aparência
        </h3>
        <div className="flex gap-2">
          {[
            { valor: "escuro" as const, label: "Escuro", icon: Moon },
            { valor: "claro" as const, label: "Claro", icon: Sun },
          ].map(op => (
            <button
              key={op.valor}
              onClick={() => atualizar("tema", op.valor)}
              className={cn(
                "flex-1 flex items-center justify-center gap-2 p-3 rounded-lg border text-sm transition-all",
                config.tema === op.valor
                  ? "bg-cyan-500/10 border-cyan-500/30 text-cyan-400"
                  : "bg-secondary/20 border-border/50 text-muted-foreground hover:bg-secondary/30"
              )}
            >
              <op.icon className="w-4 h-4" />
              {op.label}
            </button>
          ))}
        </div>
      </div>

      {/* Atualizacao */}
      <div className="rounded-xl border border-border/50 bg-secondary/10 p-5">
        <h3 className="text-sm font-bold mb-4 flex items-center gap-2">
          <Clock className="w-4 h-4 text-cyan-400" />
          Frequencia de Atualizacao
        </h3>
        <div className="flex gap-2">
          {[3, 5, 10, 30].map(seg => (
            <button
              key={seg}
              onClick={() => atualizar("frequenciaAtualizacao", seg)}
              className={cn(
                "flex-1 p-3 rounded-lg border text-sm transition-all",
                config.frequenciaAtualizacao === seg
                  ? "bg-cyan-500/10 border-cyan-500/30 text-cyan-400"
                  : "bg-secondary/20 border-border/50 text-muted-foreground hover:bg-secondary/30"
              )}
            >
              {seg}s
            </button>
          ))}
        </div>
        <p className="text-[10px] text-muted-foreground mt-2">
          Intervalo entre cada atualização dos dados do dashboard
        </p>
      </div>

      {/* Grafico */}
      <div className="rounded-xl border border-border/50 bg-secondary/10 p-5">
        <h3 className="text-sm font-bold mb-4 flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-cyan-400" />
          Grafico Padrao
        </h3>
        <div className="flex gap-2">
          {[
            { valor: "candlestick" as const, label: "Velas" },
            { valor: "line" as const, label: "Linha" },
            { valor: "area" as const, label: "Area" },
          ].map(op => (
            <button
              key={op.valor}
              onClick={() => atualizar("graficoTipo", op.valor)}
              className={cn(
                "flex-1 p-3 rounded-lg border text-sm transition-all",
                config.graficoTipo === op.valor
                  ? "bg-cyan-500/10 border-cyan-500/30 text-cyan-400"
                  : "bg-secondary/20 border-border/50 text-muted-foreground hover:bg-secondary/30"
              )}
            >
              {op.label}
            </button>
          ))}
        </div>
      </div>

      {/* Preferencias de Trading */}
      <div className="rounded-xl border border-border/50 bg-secondary/10 p-5">
        <h3 className="text-sm font-bold mb-4 flex items-center gap-2">
          <Coins className="w-4 h-4 text-cyan-400" />
          Preferências de Trading
        </h3>
        
        {/* Moeda padrao */}
        <div className="mb-4">
          <label className="text-xs text-muted-foreground mb-2 block">Moeda padrão ao iniciar</label>
          <select
            value={config.moedaPadrao}
            onChange={e => atualizar("moedaPadrao", e.target.value)}
            className="w-full bg-secondary/30 border border-border/50 rounded-lg p-2.5 text-sm"
          >
            {["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT"].map(m => (
              <option key={m} value={m}>{m.replace("USDT", "")}</option>
            ))}
          </select>
        </div>

        {/* Timeframe padrao */}
        <div>
          <label className="text-xs text-muted-foreground mb-2 block">Timeframe padrão do gráfico</label>
          <div className="flex gap-2">
            {[5, 15, 60, 300].map(tf => (
              <button
                key={tf}
                onClick={() => atualizar("timeframePadrao", tf)}
                className={cn(
                  "flex-1 p-3 rounded-lg border text-sm transition-all",
                  config.timeframePadrao === tf
                    ? "bg-cyan-500/10 border-cyan-500/30 text-cyan-400"
                    : "bg-secondary/20 border-border/50 text-muted-foreground hover:bg-secondary/30"
                )}
              >
                {tf >= 60 ? `${tf/60}min` : `${tf}s`}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Botoes */}
      <div className="flex gap-3">
        <Button onClick={salvar} className="flex-1 bg-cyan-500/20 border border-cyan-500/30 text-cyan-400 hover:bg-cyan-500/30">
          {salvo ? (
            <><Check className="w-4 h-4 mr-2" /> Salvo</>
          ) : (
            <><Save className="w-4 h-4 mr-2" /> Salvar Configurações</>
          )}
        </Button>
        <Button onClick={restaurar} variant="outline" className="flex-1">
          <RotateCcw className="w-4 h-4 mr-2" />
          Restaurar Padrão
        </Button>
      </div>
    </div>
  )
}