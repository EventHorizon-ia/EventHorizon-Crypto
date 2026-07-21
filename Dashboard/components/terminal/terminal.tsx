"use client"

import { useState, useRef, useEffect, useCallback } from "react"
import { cn } from "@/lib/utils"
import { Terminal as TerminalIcon, ChevronRight } from "lucide-react"
import { timeStamp } from "console"

interface TerminalEntry {
  id: string
  type: "input" | "output" | "error" | "system"
  content: string
  timestamp: Date
}

interface TerminalProps {
  onExecuteCommand: (command: string) => Promise<string>
  isConnected: boolean
}

const WELCOME_MESSAGE = `╔══════════════════════════════════════════════════════════════╗
║           UNIVERSE SIMULATION TERMINAL v1.0                  ║
║                                                              ║
║  Comandos disponíveis:                                       ║
║    status   - Mostra status do sistema                       ║
║    help     - Lista todos os comandos                        ║
║    clear    - Limpa o terminal                               ║
║                                                              ║
║  Digite um comando para começar...                           ║
╚══════════════════════════════════════════════════════════════╝`

export function Terminal({ onExecuteCommand, isConnected }: TerminalProps) {
    const [history, setHistory] = useState<TerminalEntry[]>(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("terminal_history")
      if (saved) {
        try {
          const parsed = JSON.parse(saved)
          return parsed.map((e: any) => ({
            ...e,
            timeStamp: new Date(e.timestamp)
          }))
        } catch {}
      }
    }

    return [
      {
        id: "welcome",
        type: "system",
        content: WELCOME_MESSAGE,
        timestamp: new Date()
      }
    ]
    })
  const [input, setInput] = useState("")
  const [commandHistory, setCommandHistory] = useState<string[]>([])
  const [historyIndex, setHistoryIndex] = useState(-1)
  const [isProcessing, setIsProcessing] = useState(false)
  
  const inputRef = useRef<HTMLInputElement>(null)
  const scrollRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = useCallback(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [history, scrollToBottom])


  useEffect(() => {
    localStorage.setItem("terminal_history", JSON.stringify(history))
  }, [history])

  const addEntry = useCallback((type: TerminalEntry["type"], content: string) => {
    setHistory(prev => [
      ...prev.slice(-99),
      {
        id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
        type,
        content,
        timestamp: new Date()
      }
    ])
  }, [])

  const handleCommand = useCallback(async (command: string) => {
    const trimmed = command.trim()
    if (!trimmed) return

    addEntry("input","> " + trimmed)
    setCommandHistory(prev => [...prev.slice(-49), trimmed])
    setHistoryIndex(-1)
    setIsProcessing(true)

    // Built-in commands
    if (trimmed.toLowerCase() === "clear") {
      setHistory([])
      setIsProcessing(false)
      return
    }


    // Send to API
    try {
      const result = await onExecuteCommand(trimmed)
      addEntry("output", result)
    } catch (err) {
      addEntry("error", `Erro: ${err instanceof Error ? err.message : "desconhecido"}`)
    }

    setIsProcessing(false)
  }, [addEntry, onExecuteCommand])

  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !isProcessing) {
      handleCommand(input)
      setInput("")
      setTimeout(() => inputRef.current?.focus(), 0)
    } else if (e.key === "ArrowUp") {
      e.preventDefault()
      if (commandHistory.length > 0) {
        const newIndex = historyIndex < commandHistory.length - 1 ? historyIndex + 1 : historyIndex
        setHistoryIndex(newIndex)
        setInput(commandHistory[commandHistory.length - 1 - newIndex] || "")
      }
    } else if (e.key === "ArrowDown") {
      e.preventDefault()
      if (historyIndex > 0) {
        const newIndex = historyIndex - 1
        setHistoryIndex(newIndex)
        setInput(commandHistory[commandHistory.length - 1 - newIndex] || "")
      } else if (historyIndex === 0) {
        setHistoryIndex(-1)
        setInput("")
      }
    }
  }, [input, isProcessing, handleCommand, commandHistory, historyIndex])

  const focusInput = useCallback(() => {
    inputRef.current?.focus()
  }, [])

  return (
    <div 
      className="h-full flex flex-col rounded-xl border border-neon-cyan/20 bg-card/80 backdrop-blur-sm overflow-hidden shadow-[0_0_30px_rgba(0,230,230,0.1)]"
      onClick={focusInput}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border/50 bg-secondary/30">
        <div className="flex items-center gap-2">
          <TerminalIcon className="h-4 w-4 text-neon-cyan" />
          <span className="text-sm font-semibold text-foreground">Terminal</span>
        </div>
        <div className="flex items-center gap-2">
          <span className={cn(
            "h-2 w-2 rounded-full",
            isConnected ? "bg-green-400" : "bg-red-400"
          )} />
          <span className="text-xs text-muted-foreground">
            {isConnected ? "Conectado" : "Desconectado"}
          </span>
        </div>
      </div>

      {/* Output */}
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 font-mono text-sm space-y-1"
      >
        {history.map((entry) => (
          <div key={entry.id} className="whitespace-pre-wrap">
            {entry.type === "input" && (
              <div className="flex items-start gap-2">
                <ChevronRight className="h-4 w-4 text-neon-cyan shrink-0 mt-0.5" />
                <span className="text-neon-cyan">{entry.content}</span>
              </div>
            )}
            {entry.type === "output" && (
              <div className="text-foreground/80 pl-6">{entry.content}</div>
            )}
            {entry.type === "error" && (
              <div className="text-red-400 pl-6">{entry.content}</div>
            )}
            {entry.type === "system" && (
              <div className="text-neon-purple/70">{entry.content}</div>
            )}
          </div>
        ))}
        {isProcessing && (
          <div className="flex items-center gap-2 text-muted-foreground">
            <span className="animate-pulse">Processando...</span>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-border/50 px-4 py-3 bg-secondary/20">
        <div className="flex items-center gap-2">
          <ChevronRight className="h-4 w-4 text-neon-cyan shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
           // disabled={isProcessing}
            placeholder="Digite um comando..."
            className="flex-1 bg-transparent text-foreground font-mono text-sm outline-none placeholder:text-muted-foreground/50"
            autoFocus
          />
        </div>
      </div>
    </div>
  )
}
