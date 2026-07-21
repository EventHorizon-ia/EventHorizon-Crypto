"use client"

import { useState, useRef, useEffect } from "react"

interface Message {
  role: "user" | "assistant"
  content: string
  id: string
  timestamp: Date
  liked?: boolean
  disliked?: boolean
}

export function ChatBot() {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  
  // Arrastar
  const [position, setPosition] = useState({ x: 0, y: 0 })
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })
  const chatRef = useRef<HTMLDivElement>(null)
  
  const [nomeTrader, setNomeTrader] = useState("Trader")
  
  // ⭐ Inicialização
  useEffect(() => {
    const saved = localStorage.getItem("trader_nome")
    if (saved) setNomeTrader(saved)
    
    const fetchNome = async () => {
      try {
        const { supabase } = await import("@/lib/supabase-client")
        const { data: { user } } = await supabase.auth.getUser()
        if (user) {
          const { data } = await supabase.from("perfis").select("nome").eq("user_id", user.id).single()
          if (data?.nome) {
            setNomeTrader(data.nome)
            localStorage.setItem("trader_nome", data.nome)
          }
        }
      } catch {}
    }
    fetchNome()
    
    // ⭐ Solicitar permissão para notificações
    if (Notification.permission === "default") {
      Notification.requestPermission()
    }
  }, [])
  
  // ⭐ Mensagem de saudação
  useEffect(() => {
    if (isOpen && messages.length === 0) {
      setMessages([{
        role: "assistant",
        content: `**Olá, ${nomeTrader}!** Sou o MenteTorch, seu assistente de IA para trading.\n\nPosso ajudar com:\n• Análise de mercado em tempo real\n• Carregar e gerenciar moedas\n• Sugestões de estratégia\n• Dúvidas sobre a plataforma\n\nComo posso ajudar hoje?`,
        id: "saudacao",
        timestamp: new Date()
      }])
    }
  }, [isOpen, nomeTrader])
  
  // ⭐ Monitorar mercado em background
  useEffect(() => {
    const checkOportunidades = async () => {
      try {
        const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://192.168.0.26:8000"
        const res = await fetch(`${API_URL}/alertas/verificar`)
        const data = await res.json()
        
        if (data.alertas && data.alertas.length > 0) {
          const alerta = data.alertas[0]
          const msg = `🚨 **Alerta automático!**\n\n${alerta.mensagem}`
          
          // Notificação do navegador
          if (Notification.permission === "granted") {
            new Notification(`🚨 ${alerta.direcao || 'SINAL'} ${alerta.moeda || ''}`, {
              body: alerta.mensagem || `${alerta.horizonte || ''} • Confiança: ${alerta.confianca || 0}%`,
              icon: "/icon.svg"
            })
          }
          
          // Adiciona no chat se estiver aberto
          if (isOpen) {
            setMessages(prev => {
              const ids = new Set(prev.map(m => m.id))
              const newId = `alerta-${Date.now()}`
              if (ids.has(newId)) return prev
              return [...prev, {
                role: "assistant",
                content: msg,
                id: newId,
                timestamp: new Date()
              }]
            })
          }
        }
      } catch {}
    }
    
    const interval = setInterval(checkOportunidades, 30000)
    return () => clearInterval(interval)
  }, [isOpen])
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }
  
  useEffect(() => {
    scrollToBottom()
  }, [messages])
  
  // ⭐ Arrastar handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).closest('[data-drag-handle]')) {
      setIsDragging(true)
      setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y })
    }
  }
  
  const handleMouseMove = (e: MouseEvent) => {
    if (isDragging) setPosition({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y })
  }
  
  const handleMouseUp = () => setIsDragging(false)
  
  useEffect(() => {
    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove)
      window.addEventListener('mouseup', handleMouseUp)
      return () => {
        window.removeEventListener('mousemove', handleMouseMove)
        window.removeEventListener('mouseup', handleMouseUp)
      }
    }
  }, [isDragging, dragStart])
  
  // ⭐ Enviar mensagem
  const sendMessage = async (text?: string) => {
    const msg = text || input
    if (!msg.trim() || loading) return
    
    const userMsg: Message = {
      role: "user",
      content: msg,
      id: Date.now().toString(),
      timestamp: new Date()
    }
    setMessages(prev => [...prev, userMsg])
    setInput("")
    setLoading(true)
    
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://192.168.0.26:8000"
      const response = await fetch(`${API_URL}/chatbot`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pergunta: msg, moeda: "BTCUSDT", nome_trader: nomeTrader })
      })
      const data = await response.json()
      
      setMessages(prev => [...prev, {
        role: "assistant",
        content: data.resposta || "Desculpe, não consegui processar.",
        id: (Date.now() + 1).toString(),
        timestamp: new Date()
      }])
    } catch {
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "**Erro de conexão.** Verifique se a API está online.",
        id: (Date.now() + 1).toString(),
        timestamp: new Date()
      }])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }
  
  // ⭐ Ações das mensagens
  const copyMessage = async (content: string, id: string) => {
    await navigator.clipboard.writeText(content)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }
  
  const regenerateMessage = async (index: number) => {
    if (index === 0) return
    const userMsg = messages[index - 1]
    if (userMsg.role !== "user") return
    setMessages(prev => prev.filter((_, i) => i !== index))
    sendMessage(userMsg.content)
  }
  
  const likeMessage = (id: string) => {
    setMessages(prev => prev.map(msg => 
      msg.id === id ? { ...msg, liked: true, disliked: false } : msg
    ))
  }
  
  const dislikeMessage = (id: string) => {
    setMessages(prev => prev.map(msg => 
      msg.id === id ? { ...msg, disliked: true, liked: false } : msg
    ))
  }
  
  // ⭐ Formatação
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })
  }
  
  const renderContent = (content: string) => {
    return content
      .split('\n')
      .map((line) => {
        let html = line.replace(/\*\*(.*?)\*\*/g, '<strong class="text-cyan-400 font-semibold">$1</strong>')
        if (line.trim().startsWith('•')) {
          html = `<span class="text-cyan-400">•</span> ${html.replace('•', '').trim()}`
        }
        return html
      })
      .join('<br/>')
  }
  
  return (
    <>
      {/* ⭐ Botão flutuante */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-2xl bg-neutral-800 border border-neutral-700 text-neutral-300 shadow-2xl flex items-center justify-center hover:bg-neutral-700 hover:text-white transition-all active:scale-95"
        title="MenteTorch Assistant"
      >
        {isOpen ? (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        ) : (
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <circle cx="12" cy="12" r="10"/><circle cx="12" cy="6.5" r="1.8" fill="currentColor"/>
            <path d="M6.5 17V10l3 5 2.5-5 2.5 5 3-5v7" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        )}
      </button>
      
      {/* ⭐ Janela do chat */}
      {isOpen && (
        <div
          ref={chatRef}
          onMouseDown={handleMouseDown}
          style={{
            position: 'fixed',
            left: position.x || undefined,
            top: position.y || undefined,
            bottom: position.x === 0 && position.y === 0 ? '5.5rem' : undefined,
            right: position.x === 0 && position.y === 0 ? '1.5rem' : undefined,
            zIndex: 50,
            width: '400px',
            height: '560px',
            cursor: isDragging ? 'grabbing' : 'default',
          }}
          className="bg-[#0a0a0a] border border-neutral-800 rounded-2xl shadow-2xl flex flex-col overflow-hidden"
        >
          {/* Header */}
          <div 
            data-drag-handle
            className="px-4 py-3 border-b border-neutral-800 flex items-center gap-3 bg-[#0f0f0f] cursor-grab active:cursor-grabbing select-none"
          >
            <div className="w-10 h-10 rounded-xl bg-neutral-800 flex items-center justify-center">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#06b6d4" strokeWidth="1.5">
                <circle cx="12" cy="12" r="10"/><circle cx="12" cy="6.5" r="1.5" fill="#06b6d4"/>
                <path d="M7 17V10l2.5 5 2.5-5 2.5 5 2.5-5v7" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <div className="flex-1">
              <h3 className="text-sm font-semibold text-neutral-200">MenteTorch</h3>
              <p className="text-[10px] text-neutral-500">Groq • Llama 3.1 • Monitorando</p>
            </div>
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <button 
              onClick={() => setIsOpen(false)}
              className="p-1.5 rounded-lg hover:bg-neutral-800 text-neutral-500 hover:text-neutral-300 transition-colors ml-1"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>
          
          {/* Mensagens */}
          <div className="flex-1 overflow-y-auto px-4 py-4 space-y-5">
            {messages.map((msg, i) => (
              <div key={msg.id} className="group">
                <div className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[85%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed ${
                    msg.role === 'user' 
                      ? 'bg-neutral-800 text-neutral-200 rounded-br-md' 
                      : 'bg-neutral-900 text-neutral-300 rounded-bl-md border border-neutral-800'
                  }`}
                    dangerouslySetInnerHTML={{ __html: renderContent(msg.content) }}
                  />
                </div>
                
                {/* ⭐ Botões de ação + horário */}
                <div className={`flex items-center gap-1 mt-1 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  {msg.role === 'assistant' && (
                    <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button onClick={() => copyMessage(msg.content, msg.id)} className="p-1 rounded hover:bg-neutral-800 text-neutral-600 hover:text-neutral-300 transition-colors" title="Copiar">
                        {copiedId === msg.id ? (
                          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="2"><polyline points="20 6 9 17 4 12"/></svg>
                        ) : (
                          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                        )}
                      </button>
                      <button onClick={() => regenerateMessage(i)} className="p-1 rounded hover:bg-neutral-800 text-neutral-600 hover:text-neutral-300 transition-colors" title="Refazer">
                        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
                      </button>
                      <button onClick={() => likeMessage(msg.id)} className={`p-1 rounded transition-colors ${msg.liked ? 'text-emerald-400 bg-emerald-500/10' : 'text-neutral-600 hover:text-neutral-300 hover:bg-neutral-800'}`} title="Gostei">
                        <svg width="11" height="11" viewBox="0 0 24 24" fill={msg.liked ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/></svg>
                      </button>
                      <button onClick={() => dislikeMessage(msg.id)} className={`p-1 rounded transition-colors ${msg.disliked ? 'text-red-400 bg-red-500/10' : 'text-neutral-600 hover:text-neutral-300 hover:bg-neutral-800'}`} title="Não gostei">
                        <svg width="11" height="11" viewBox="0 0 24 24" fill={msg.disliked ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2"><path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3H10zM17 2h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"/></svg>
                      </button>
                    </div>
                  )}
                  <span className="text-[10px] text-neutral-600 ml-1">
                    {formatTime(msg.timestamp)}
                  </span>
                </div>
              </div>
            ))}
            
            {loading && (
              <div className="flex justify-start">
                <div className="bg-neutral-900 border border-neutral-800 rounded-2xl rounded-bl-md px-4 py-3 flex gap-1.5">
                  <div className="w-2 h-2 rounded-full bg-neutral-600 animate-bounce" />
                  <div className="w-2 h-2 rounded-full bg-neutral-600 animate-bounce" style={{animationDelay: '0.15s'}} />
                  <div className="w-2 h-2 rounded-full bg-neutral-600 animate-bounce" style={{animationDelay: '0.3s'}} />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
          
          {/* Sugestões */}
          {messages.length <= 1 && (
            <div className="px-4 pb-2">
              <div className="flex flex-wrap gap-1.5">
                {["Carregar BTC", "Análise do mercado", "Iniciar sistema", "Melhor horizonte"].map(sug => (
                  <button
                    key={sug}
                    onClick={() => sendMessage(sug)}
                    className="text-xs px-3 py-1.5 rounded-full border border-neutral-800 text-neutral-400 hover:text-neutral-200 hover:border-neutral-700 transition-all"
                  >
                    {sug}
                  </button>
                ))}
              </div>
            </div>
          )}
          
          {/* Input */}
          <div className="p-3 border-t border-neutral-800 bg-[#0f0f0f]">
            <div className="flex gap-2">
              <input
                ref={inputRef}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && sendMessage()}
                placeholder="Pergunte algo..."
                className="flex-1 bg-neutral-900 border border-neutral-800 rounded-xl px-3.5 py-2.5 text-sm text-neutral-200 placeholder-neutral-600 outline-none focus:border-neutral-600 transition-colors"
                disabled={loading}
              />
              <button 
                onClick={() => sendMessage()}
                disabled={loading || !input.trim()}
                className="px-3 rounded-xl bg-neutral-800 hover:bg-neutral-700 text-neutral-400 hover:text-white transition-colors disabled:opacity-30"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}