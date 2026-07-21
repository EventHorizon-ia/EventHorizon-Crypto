// app/alertas/page.tsx
"use client"

import { useState, useEffect } from "react"
import {
  Bell, BellRing, Shield, Zap, TrendingUp, TrendingDown,
  Clock, Settings, Trash2, Plus, CheckCircle2, XCircle,
  Loader2, RefreshCw, Play, Pause, AlertTriangle,
  Circle, X
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { API_BASE_URL } from "@/lib/api"

// ============================================
// TIPOS
// ============================================

interface AlertaSinal {
  moeda: string
  direcao: string
  horizonte: string
  confianca_min: number
  ativo: boolean
}

interface AlertaConfig {
  sinais: AlertaSinal[]
  protecao: {
    drawdown_max: number
    losses_seguidos: number
    volume_anormal: number
    acuracia_min: number
    pausar_apos_losses: boolean
  }
  oportunidades: {
    acuracia_alta: number
    melhor_horario: boolean
    nova_moeda: number
  }
  canais: {
    navegador: boolean
    telegram: boolean
    email: boolean
    som: boolean
  }
}

interface StatusAtual {
  drawdown_atual: number
  losses_seguidos: number
  acuracia_atual: number
  volume_atual: number
}

interface AlertaHistorico {
  tipo: string
  moeda?: string
  direcao?: string
  horizonte?: string
  previsao?: number
  confianca?: number
  timestamp: number
  mensagem: string
}

// ============================================
// COMPONENTE
// ============================================

export default function AlertasPage() {
  const [config, setConfig] = useState<AlertaConfig | null>(null)
  const [statusAtual, setStatusAtual] = useState<StatusAtual | null>(null)
  const [historico, setHistorico] = useState<AlertaHistorico[]>([])
  const [alertasAtivos, setAlertasAtivos] = useState<AlertaHistorico[]>([])
  const [loading, setLoading] = useState(true)
  const [verificando, setVerificando] = useState(false)
  const [salvando, setSalvando] = useState(false)
  
  // Modal
  const [showAddModal, setShowAddModal] = useState(false)
  const [novoAlerta, setNovoAlerta] = useState({
    moeda: "BTC",
    direcao: "COMPRAR",
    horizonte: "5min",
    confianca_min: 60
  })

  useEffect(() => {
    carregarTudo()
  }, [])

  async function carregarTudo() {
    try {
      const [resConfig, resHistorico, resStatus] = await Promise.all([
        fetch(`${API_BASE_URL}/alertas/config`),
        fetch(`${API_BASE_URL}/alertas/historico?limit=20`),
        fetch(`${API_BASE_URL}/alertas/status-atual`)
      ])
      setConfig(await resConfig.json())
      const hist = await resHistorico.json()
      setHistorico(hist.alertas || [])
      setStatusAtual(await resStatus.json())
    } catch (e) {
      console.error("Erro ao carregar:", e)
    } finally {
      setLoading(false)
    }
  }

  async function verificarAgora() {
  setVerificando(true)
  try {
    const res = await fetch(`${API_BASE_URL}/alertas/verificar`)
    const data = await res.json()
    console.log("🔔 Resposta do /alertas/verificar:", data)
    setAlertasAtivos(data.alertas || [])
    
    // Recarrega tudo
    await carregarTudo()
    
    // Feedback visual
    if (!data.alertas || data.alertas.length === 0) {
      alert("✅ Nenhum alerta no momento. O mercado está estável ou os sinais não atingiram os thresholds mínimos.")
    }
  } catch (e) {
    console.error("❌ Erro ao verificar:", e)
    alert("❌ Erro ao conectar com a API. O servidor está rodando?")
  } finally {
    setVerificando(false)
  }
}

  async function salvarConfig() {
  if (!config) return
  setSalvando(true)
  console.log("💾 Salvando configurações:", config)
  try {
    const res = await fetch(`${API_BASE_URL}/alertas/salvar`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config)
    })
    const data = await res.json()
    console.log("✅ Configurações salvas:", data)
    alert("✅ Configurações salvas com sucesso!")
  } catch (e) {
    console.error("❌ Erro ao salvar:", e)
    alert("❌ Erro ao salvar. O servidor está rodando?")
  } finally {
    setSalvando(false)
  }
}

  function toggleSinal(index: number) {
    if (!config) return
    const nova = { ...config }
    nova.sinais[index].ativo = !nova.sinais[index].ativo
    setConfig(nova)
    salvarConfig()
  }

  function removerSinal(index: number) {
    if (!config) return
    const nova = { ...config }
    nova.sinais.splice(index, 1)
    setConfig(nova)
    salvarConfig()
  }

  function adicionarSinal() {
    if (!config) return
    const nova = { ...config }
    nova.sinais.push({ ...novoAlerta, ativo: true })
    setConfig(nova)
    setShowAddModal(false)
    salvarConfig()
  }

  // Status geral
  function getStatusGeral() {
    if (!config || !statusAtual) return { texto: "Carregando...", cor: "text-gray-400", bg: "bg-gray-500/10", icone: Loader2 }
    
    const violacoes = []
    if (statusAtual.drawdown_atual <= config.protecao.drawdown_max) violacoes.push("Drawdown")
    if (statusAtual.losses_seguidos >= config.protecao.losses_seguidos) violacoes.push("Losses")
    if (statusAtual.acuracia_atual < config.protecao.acuracia_min) violacoes.push("Acurácia")
    
    if (violacoes.length === 0) return { texto: "TUDO DENTRO DO NORMAL", cor: "text-green-400", bg: "bg-green-500/10 border-green-500/20", icone: CheckCircle2 }
    if (violacoes.length === 1) return { texto: `ATENÇÃO: ${violacoes[0]}`, cor: "text-yellow-400", bg: "bg-yellow-500/10 border-yellow-500/20", icone: AlertTriangle }
    return { texto: `CRÍTICO: ${violacoes.join(", ")}`, cor: "text-red-400", bg: "bg-red-500/10 border-red-500/20", icone: XCircle }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-4rem)]">
        <Loader2 className="w-8 h-8 animate-spin text-cyan-400" />
      </div>
    )
  }

  const statusGeral = getStatusGeral()
  const IconeStatus = statusGeral.icone

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Alertas</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Configure notificações inteligentes baseadas na IA
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={verificarAgora} disabled={verificando} className="bg-cyan-500/20 border border-cyan-500/30 text-cyan-400 hover:bg-cyan-500/30">
            {verificando ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <RefreshCw className="w-4 h-4 mr-2" />}
            VERIFICAR AGORA
          </Button>
          <Button onClick={salvarConfig} disabled={salvando} className="bg-green-500/20 border border-green-500/30 text-green-400 hover:bg-green-500/30">
            {salvando ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <CheckCircle2 className="w-4 h-4 mr-2" />}
            SALVAR
          </Button>
        </div>
      </div>

      {/* Status Geral */}
      <div className={cn("rounded-xl p-4 border", statusGeral.bg)}>
        <div className="flex items-center gap-2">
          <IconeStatus className={cn("w-5 h-5", statusGeral.cor)} />
          <span className={cn("text-sm font-bold", statusGeral.cor)}>{statusGeral.texto}</span>
        </div>
      </div>

      {/* Alertas Encontrados AGORA */}
      {alertasAtivos.length > 0 && (
        <div className="rounded-xl border border-green-500/20 bg-green-500/5 p-4">
          <h3 className="text-sm font-bold text-green-400 mb-3 flex items-center gap-2">
            <BellRing className="w-4 h-4" />
            ALERTAS DISPARADOS ({alertasAtivos.length})
          </h3>
          <div className="space-y-2">
            {alertasAtivos.map((alerta, i) => (
              <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-green-500/10 border border-green-500/20">
                <div className="flex items-center gap-3">
                  {alerta.direcao === "COMPRAR" ? (
                    <TrendingUp className="w-4 h-4 text-green-400" />
                  ) : (
                    <TrendingDown className="w-4 h-4 text-red-400" />
                  )}
                  <div>
                    <p className="text-sm font-medium">{alerta.mensagem}</p>
                    <p className="text-[10px] text-muted-foreground">
                      Previsão: {alerta.previsao}% • Confiança: {alerta.confianca}%
                    </p>
                  </div>
                </div>
                <span className={cn(
                  "px-2 py-0.5 rounded text-[10px] font-bold",
                  alerta.direcao === "COMPRAR" ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"
                )}>
                  {alerta.direcao}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-6">
        {/* Sinais */}
        <div className="rounded-xl border border-border/50 bg-secondary/10 p-4">
          <h3 className="text-sm font-bold flex items-center gap-2 mb-4">
            <TrendingUp className="w-4 h-4 text-cyan-400" />
            Alertas de Sinais
          </h3>
          
          {config?.sinais.map((sinal, i) => (
            <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-secondary/20 mb-2">
              <div className="flex items-center gap-3">
                <button onClick={() => toggleSinal(i)}>
                  {sinal.ativo ? (
                    <CheckCircle2 className="w-5 h-5 text-green-400 hover:text-green-300" />
                  ) : (
                    <XCircle className="w-5 h-5 text-gray-500 hover:text-gray-400" />
                  )}
                </button>
                <div>
                  <p className="text-sm font-medium">{sinal.moeda} • {sinal.direcao}</p>
                  <p className="text-[10px] text-muted-foreground">
                    {sinal.horizonte} • Conf mín: {sinal.confianca_min}%
                  </p>
                </div>
              </div>
              <button onClick={() => removerSinal(i)} className="text-gray-500 hover:text-red-400">
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
          
          <Button onClick={() => setShowAddModal(true)} className="w-full mt-2 bg-secondary/30 border border-border/50 hover:bg-secondary/50 text-xs">
            <Plus className="w-3 h-3 mr-2" />
            Adicionar Alerta
          </Button>
        </div>

        {/* Proteção + Status Atual */}
        <div className="rounded-xl border border-border/50 bg-secondary/10 p-4">
          <h3 className="text-sm font-bold flex items-center gap-2 mb-4">
            <Shield className="w-4 h-4 text-yellow-400" />
            Alertas de Proteção
          </h3>
          
          {config && statusAtual && (
            <div className="space-y-3">
              {[
                { 
                  label: "Drawdown máximo", 
                  config: `${config.protecao.drawdown_max}%`, 
                  atual: `${statusAtual.drawdown_atual}%`,
                  ok: statusAtual.drawdown_atual > config.protecao.drawdown_max
                },
                { 
                  label: "Losses seguidos", 
                  config: config.protecao.losses_seguidos, 
                  atual: statusAtual.losses_seguidos,
                  ok: statusAtual.losses_seguidos < config.protecao.losses_seguidos
                },
                { 
                  label: "Volume anormal", 
                  config: `+${config.protecao.volume_anormal}%`, 
                  atual: `+${statusAtual.volume_atual}%`,
                  ok: statusAtual.volume_atual < config.protecao.volume_anormal
                },
                { 
                  label: "Acurácia mínima", 
                  config: `${config.protecao.acuracia_min}%`, 
                  atual: `${statusAtual.acuracia_atual}%`,
                  ok: statusAtual.acuracia_atual >= config.protecao.acuracia_min
                },
              ].map((item, i) => (
                <div key={i} className="p-3 rounded-lg bg-secondary/20">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-xs text-muted-foreground">{item.label}</span>
                    {item.ok ? (
                      <CheckCircle2 className="w-4 h-4 text-green-400" />
                    ) : (
                      <AlertTriangle className="w-4 h-4 text-red-400" />
                    )}
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-muted-foreground">Limite: <strong>{item.config}</strong></span>
                    <span className="text-muted-foreground">•</span>
                    <span className={item.ok ? "text-green-400" : "text-red-400"}>
                      Atual: <strong>{item.atual}</strong> {item.ok ? "✅" : "🔴"}
                    </span>
                  </div>
                </div>
              ))}
              
              <div className="flex justify-between items-center p-3 rounded-lg bg-secondary/20">
                <span className="text-xs">Pausar após losses</span>
                <span className={config.protecao.pausar_apos_losses ? "text-green-400 font-bold" : "text-gray-500"}>
                  {config.protecao.pausar_apos_losses ? "SIM" : "NÃO"}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Canais */}
      <div className="rounded-xl border border-border/50 bg-secondary/10 p-4">
        <h3 className="text-sm font-bold flex items-center gap-2 mb-4">
          <Bell className="w-4 h-4 text-purple-400" />
          Canais de Notificação
        </h3>
        <div className="grid grid-cols-4 gap-3">
          {config && [
            { label: "Navegador", valor: config.canais.navegador, icon: BellRing },
            { label: "Telegram", valor: config.canais.telegram, icon: Zap },
            { label: "Email", valor: config.canais.email, icon: Bell },
            { label: "Som", valor: config.canais.som, icon: Bell },
          ].map((canal, i) => (
            <div key={i} className={cn(
              "rounded-lg p-3 text-center border",
              canal.valor ? "bg-green-500/10 border-green-500/20" : "bg-secondary/20 border-border/50"
            )}>
              <canal.icon className={cn("w-5 h-5 mx-auto mb-1", canal.valor ? "text-green-400" : "text-gray-500")} />
              <p className="text-xs">{canal.label}</p>
              <p className={cn("text-[10px]", canal.valor ? "text-green-400" : "text-gray-500")}>
                {canal.valor ? "ATIVO" : "INATIVO"}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Histórico */}
      <div className="rounded-xl border border-border/50 bg-secondary/10 p-4">
        <h3 className="text-sm font-bold flex items-center gap-2 mb-4">
          <Clock className="w-4 h-4 text-cyan-400" />
          Histórico de Alertas
        </h3>
        
        {historico.length > 0 ? (
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {[...historico].reverse().map((alerta, i) => (
              <div key={i} className="flex items-center justify-between p-2 rounded bg-secondary/20">
                <div className="flex items-center gap-2">
                  {alerta.direcao === "COMPRAR" ? (
                    <TrendingUp className="w-3 h-3 text-green-400" />
                  ) : alerta.direcao === "VENDER" ? (
                    <TrendingDown className="w-3 h-3 text-red-400" />
                  ) : (
                    <Shield className="w-3 h-3 text-yellow-400" />
                  )}
                  <span className="text-xs">{alerta.mensagem}</span>
                </div>
                <span className="text-[10px] text-muted-foreground">
                  {new Date(alerta.timestamp * 1000).toLocaleTimeString("pt-BR")}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-muted-foreground">
            <Bell className="w-8 h-8 mx-auto mb-2 opacity-30" />
            <p className="text-sm">Nenhum alerta gerado ainda</p>
            <p className="text-xs mt-1">Clique em VERIFICAR AGORA para buscar sinais</p>
          </div>
        )}
      </div>

      {/* Modal Adicionar Alerta */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
          <div className="bg-[#0a0f1a] rounded-xl p-6 w-96 border border-border shadow-2xl">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-bold">Novo Alerta de Sinal</h3>
              <button onClick={() => setShowAddModal(false)} className="text-muted-foreground hover:text-foreground">
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="space-y-3">
              <div>
                <label className="text-xs text-muted-foreground">Moeda</label>
                <select 
                  value={novoAlerta.moeda} 
                  onChange={e => setNovoAlerta({...novoAlerta, moeda: e.target.value})}
                  className="w-full bg-secondary/30 rounded-lg p-2.5 text-sm mt-1 border border-border/50"
                >
                  <option>BTC</option>
                  <option>ETH</option>
                  <option>BNB</option>
                  <option>SOL</option>
                  <option>DOGE</option>
                </select>
              </div>
              
              <div>
                <label className="text-xs text-muted-foreground">Direção</label>
                <select 
                  value={novoAlerta.direcao} 
                  onChange={e => setNovoAlerta({...novoAlerta, direcao: e.target.value})}
                  className="w-full bg-secondary/30 rounded-lg p-2.5 text-sm mt-1 border border-border/50"
                >
                  <option>COMPRAR</option>
                  <option>VENDER</option>
                </select>
              </div>
              
              <div>
                <label className="text-xs text-muted-foreground">Horizonte</label>
                <select 
                  value={novoAlerta.horizonte} 
                  onChange={e => setNovoAlerta({...novoAlerta, horizonte: e.target.value})}
                  className="w-full bg-secondary/30 rounded-lg p-2.5 text-sm mt-1 border border-border/50"
                >
                  <option>5s</option>
                  <option>15s</option>
                  <option>30s</option>
                  <option>1min</option>
                  <option>5min</option>
                  <option>15min</option>
                  <option>30min</option>
                  <option>1h</option>
                </select>
              </div>
              
              <div>
                <label className="text-xs text-muted-foreground">
                  Confiança Mínima: <strong className="text-cyan-400">{novoAlerta.confianca_min}%</strong>
                </label>
                <input 
                  type="range" 
                  value={novoAlerta.confianca_min} 
                  onChange={e => setNovoAlerta({...novoAlerta, confianca_min: Number(e.target.value)})}
                  min={30} max={90} step={5}
                  className="w-full h-2 rounded-full bg-secondary/50 accent-cyan-400 mt-2"
                />
                <div className="flex justify-between text-[10px] text-muted-foreground mt-1">
                  <span>30%</span>
                  <span>90%</span>
                </div>
              </div>
            </div>
            
            <div className="flex gap-2 mt-6">
              <Button onClick={() => setShowAddModal(false)} variant="outline" className="flex-1">
                Cancelar
              </Button>
              <Button onClick={adicionarSinal} className="flex-1 bg-cyan-500/20 text-cyan-400 hover:bg-cyan-500/30 border border-cyan-500/30">
                <Plus className="w-4 h-4 mr-2" />
                Adicionar
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}