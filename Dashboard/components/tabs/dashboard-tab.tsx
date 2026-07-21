// components/tabs/dashboard-tab.tsx
"use client"

import { useState, useEffect } from "react"

import { API_BASE_URL } from "@/lib/api"
const API_BASE = API_BASE_URL

export function DashboardTab() {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(`${API_BASE}/dashboard/realtime`)
        const json = await response.json()
        setData(json)
      } catch (e) {
        console.error(e)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [])

  if (loading) return (
    <div className="flex items-center justify-center py-20">
      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-cyan-400" />
      <span className="ml-3 text-sm text-muted-foreground">Carregando dados em tempo real...</span>
    </div>
  )
  
  if (!data || data.total_moedas === 0) return (
    <div className="text-center py-20 text-muted-foreground">
      <p className="text-lg font-medium">Nenhuma moeda carregada</p>
      <p className="text-sm mt-2">Carregue moedas na aba Crypto Trading para ver os dados aqui.</p>
    </div>
  )

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold">Dashboard</h2>
          <p className="text-xs text-muted-foreground">
            {data.total_moedas} moeda(s) • {data.total_verificacoes?.toLocaleString()} trades verificados
          </p>
        </div>
        {data.melhor_moeda && (
          <div className="text-right">
            <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Melhor Oportunidade</p>
            <p className="text-sm font-bold text-green-400">
              {data.melhor_moeda.symbol} • {data.melhor_moeda.acuracias_reais?.['900']?.acuracia ?? '?'}% acc 15min
            </p>
          </div>
        )}
      </div>

      {/* Tabela Principal: Acurácia REAL por Horizonte */}
      <div className="rounded-lg border border-border/50 overflow-hidden">
        <div className="bg-secondary/30 px-4 py-2.5 flex items-center justify-between">
          <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Acurácia Real por Horizonte
          </span>
          <span className="text-[10px] text-muted-foreground">
            Verificado com preços reais após cada horizonte
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-border/50 text-muted-foreground bg-secondary/10">
                <th className="text-left p-2.5 font-medium">Moeda</th>
                <th className="text-right p-2.5 w-14">5s</th>
                <th className="text-right p-2.5 w-14">15s</th>
                <th className="text-right p-2.5 w-14">30s</th>
                <th className="text-right p-2.5 w-14">60s</th>
                <th className="text-right p-2.5 w-14">5min</th>
                <th className="text-right p-2.5 w-14">15min</th>
                <th className="text-right p-2.5 w-14">30min</th>
                <th className="text-right p-2.5 w-14">1h</th>
                <th className="text-right p-2.5 w-20">Gerações</th>
              </tr>
            </thead>
            <tbody>
              {data.moedas.map((m: any, idx: number) => (
                <tr key={m.symbol} className={`border-b border-border/20 hover:bg-secondary/20 transition-colors ${idx === 0 ? 'bg-green-500/5' : ''}`}>
                  <td className="p-2.5 font-medium">
                    <span className="text-foreground">{m.symbol}</span>
                    <span className="text-[10px] text-muted-foreground ml-1.5">
                      ${m.price?.toLocaleString()}
                    </span>
                    {idx === 0 && (
                      <span className="ml-1 text-[9px] text-green-400 font-medium">★</span>
                    )}
                  </td>
                  {['5','15','30','60','300','900','1800','3600'].map(h => {
                    const acc = m.acuracias_reais?.[h]
                    const val = acc?.acuracia ?? null
                    const total = acc?.total ?? 0
                    
                    if (val === null) {
                      return (
                        <td key={h} className="p-2.5 text-right text-muted-foreground/50" title="Dados insuficientes">
                          —
                        </td>
                      )
                    }
                    
                    const color = val >= 55 ? 'text-green-400' : val >= 48 ? 'text-yellow-400' : 'text-red-400'
                    const bg = val >= 55 ? 'bg-green-500/10' : val >= 48 ? 'bg-yellow-500/10' : ''
                    
                    return (
                      <td key={h} className={`p-2.5 text-right font-mono font-medium ${color} ${bg} rounded`}
                        title={`${acc?.acertos ?? 0} acertos / ${total} trades`}>
                        {val}%
                      </td>
                    )
                  })}
                  <td className="p-2.5 text-right text-muted-foreground tabular-nums">
                    {m.geracoes?.toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Grid Inferior: Previsões + Melhores Horários */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Previsões Atuais */}
        <div className="rounded-lg border border-border/50 overflow-hidden">
          <div className="bg-secondary/30 px-4 py-2.5">
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Previsões em Tempo Real
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-border/50 text-muted-foreground bg-secondary/10">
                  <th className="text-left p-2.5 font-medium">Moeda</th>
                  <th className="text-right p-2.5">5s</th>
                  <th className="text-right p-2.5">60s</th>
                  <th className="text-right p-2.5">5min</th>
                  <th className="text-right p-2.5">15min</th>
                  <th className="text-right p-2.5">1h</th>
                  <th className="text-right p-2.5">1d</th>
                  <th className="text-right p-2.5">RSI</th>
                  <th className="text-right p-2.5">Regime</th>
                </tr>
              </thead>
              <tbody>
                {data.moedas.map((m: any) => (
                  <tr key={m.symbol} className="border-b border-border/20 hover:bg-secondary/20 transition-colors">
                    <td className="p-2.5 font-medium">{m.symbol}</td>
                    <td className={`p-2.5 text-right font-mono ${(m.previsoes?.['5s'] || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {(m.previsoes?.['5s'] || 0) > 0 ? '+' : ''}{m.previsoes?.['5s']?.toFixed(2)}%
                    </td>
                    <td className={`p-2.5 text-right font-mono ${(m.previsoes?.['60s'] || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {(m.previsoes?.['60s'] || 0) > 0 ? '+' : ''}{m.previsoes?.['60s']?.toFixed(2)}%
                    </td>
                    <td className={`p-2.5 text-right font-mono ${(m.previsoes?.['5min'] || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {(m.previsoes?.['5min'] || 0) > 0 ? '+' : ''}{m.previsoes?.['5min']?.toFixed(2)}%
                    </td>
                    <td className={`p-2.5 text-right font-mono font-bold ${(m.previsoes?.['15min'] || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {(m.previsoes?.['15min'] || 0) > 0 ? '+' : ''}{m.previsoes?.['15min']?.toFixed(2)}%
                    </td>
                    <td className={`p-2.5 text-right font-mono ${(m.previsoes?.['1h'] || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {(m.previsoes?.['1h'] || 0) > 0 ? '+' : ''}{m.previsoes?.['1h']?.toFixed(2)}%
                    </td>
                    <td className={`p-2.5 text-right font-mono ${(m.previsoes?.['1d'] || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {(m.previsoes?.['1d'] || 0) > 0 ? '+' : ''}{m.previsoes?.['1d']?.toFixed(2)}%
                    </td>
                    <td className="p-2.5 text-right font-mono">{m.rsi}</td>
                    <td className="p-2.5 text-right">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] ${
                        m.regime === 'trend_up' ? 'bg-green-500/10 text-green-400' :
                        m.regime === 'trend_down' ? 'bg-red-500/10 text-red-400' :
                        m.regime === 'volatile' ? 'bg-yellow-500/10 text-yellow-400' :
                        'bg-gray-500/10 text-gray-400'
                      }`}>
                        {m.regime === 'trend_up' ? 'Alta' :
                         m.regime === 'trend_down' ? 'Baixa' :
                         m.regime === 'volatile' ? 'Volátil' : 'Lateral'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Melhores Horários para Operar (Brasil) */}
        <div className="rounded-lg border border-border/50 overflow-hidden">
          <div className="bg-secondary/30 px-4 py-2.5">
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Melhores Horários (Horário de Brasília)
            </span>
          </div>
          <div className="p-4 space-y-4">
            {/* Horários Recomendados */}
            <div>
              <p className="text-[10px] text-muted-foreground mb-2 uppercase tracking-wider">Recomendados para Operar</p>
              <div className="space-y-2">
                {[
                  { hora: '10:00 - 11:00', motivo: 'Abertura do mercado europeu', qualidade: 'Ótimo', cor: 'text-green-400', bg: 'bg-green-500/10' },
                  { hora: '14:00 - 16:00', motivo: 'Abertura do mercado americano', qualidade: 'Ótimo', cor: 'text-green-400', bg: 'bg-green-500/10' },
                  { hora: '08:00 - 09:00', motivo: 'Fechamento asiático + início europeu', qualidade: 'Bom', cor: 'text-cyan-400', bg: 'bg-cyan-500/10' },
                  { hora: '16:00 - 17:00', motivo: 'Fechamento europeu + EUA ativo', qualidade: 'Bom', cor: 'text-cyan-400', bg: 'bg-cyan-500/10' },
                ].map((h, i) => (
                  <div key={i} className={`flex items-center justify-between p-2.5 rounded-lg ${h.bg} border border-border/30`}>
                    <div>
                      <p className={`text-sm font-bold ${h.cor}`}>{h.hora}</p>
                      <p className="text-[10px] text-muted-foreground">{h.motivo}</p>
                    </div>
                    <span className={`text-[10px] font-medium ${h.cor}`}>{h.qualidade}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Horários para Evitar */}
            <div>
              <p className="text-[10px] text-muted-foreground mb-2 uppercase tracking-wider">Evitar</p>
              <div className="space-y-2">
                {[
                  { hora: '12:00 - 13:00', motivo: 'Almoço - baixa liquidez' },
                  { hora: '18:00 - 19:00', motivo: 'Transição de pregões' },
                  { hora: '00:00 - 06:00', motivo: 'Madrugada - volume muito baixo' },
                ].map((h, i) => (
                  <div key={i} className="flex items-center justify-between p-2.5 rounded-lg bg-red-500/5 border border-red-500/10">
                    <div>
                      <p className="text-sm font-medium text-red-400/80">{h.hora}</p>
                      <p className="text-[10px] text-muted-foreground">{h.motivo}</p>
                    </div>
                    <span className="text-[10px] text-red-400/60">Evitar</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="text-[10px] text-muted-foreground text-center pt-2 border-t border-border/30">
              Baseado em padrões históricos de volume e volatilidade. Horário de Brasília (GMT-3).
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="text-center text-[10px] text-muted-foreground py-2">
        Dados atualizados a cada 5 segundos. Acurácia real verificada comparando previsões com preços reais após cada horizonte.
      </div>
    </div>
  )
}