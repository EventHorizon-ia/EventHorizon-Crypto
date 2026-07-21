// components/AlertasToast.tsx
"use client"

import { useEffect, useState } from "react"
import { BellRing, TrendingUp, TrendingDown, X, Shield, ArrowRight } from "lucide-react"
import { useRouter } from "next/navigation"
import { cn } from "@/lib/utils"
import { useAlertas } from "@/contexts/AlertasContext"

export function AlertasToast() {
  const { ultimoAlerta, marcarLido } = useAlertas()
  const [visivel, setVisivel] = useState(false)
  const [saindo, setSaindo] = useState(false)
  const router = useRouter()

  useEffect(() => {
    if (ultimoAlerta && !ultimoAlerta.lido) {
      setVisivel(true)
      setSaindo(false)
      
      // Auto-esconde após 5 segundos
      const timer = setTimeout(() => {
        setSaindo(true)
        setTimeout(() => {
          setVisivel(false)
          marcarLido(ultimoAlerta.id)
        }, 300)
      }, 5000)
      
      return () => clearTimeout(timer)
    }
  }, [ultimoAlerta, marcarLido])

  if (!visivel || !ultimoAlerta) return null

  const isCompra = ultimoAlerta.direcao === "COMPRAR"

  return (
    <div className={cn(
      "fixed bottom-6 right-6 z-50 max-w-sm transition-all duration-300",
      saindo ? "opacity-0 translate-y-4" : "opacity-100 translate-y-0"
    )}>
      <div className={cn(
        "rounded-xl p-4 shadow-2xl border backdrop-blur-sm",
        isCompra 
          ? "bg-green-500/10 border-green-500/30 shadow-green-500/20" 
          : "bg-red-500/10 border-red-500/30 shadow-red-500/20"
      )}>
        <div className="flex items-start gap-3">
          {/* Ícone */}
          <div className={cn(
            "flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center",
            isCompra ? "bg-green-500/20" : "bg-red-500/20"
          )}>
            {isCompra ? (
              <TrendingUp className="w-5 h-5 text-green-400" />
            ) : (
              <TrendingDown className="w-5 h-5 text-red-400" />
            )}
          </div>
          
          {/* Conteúdo */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <BellRing className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
              <span className="text-xs font-medium text-cyan-400">ALERTA DE SINAL</span>
            </div>
            <p className="text-sm font-bold text-foreground">
              {ultimoAlerta.direcao} {ultimoAlerta.moeda}
            </p>
            <p className="text-xs text-muted-foreground mt-0.5">
              {ultimoAlerta.horizonte} • Confiança: {ultimoAlerta.confianca}%
            </p>
            
            <button
              onClick={() => {
                router.push("/alertas")
                setVisivel(false)
                marcarLido(ultimoAlerta.id)
              }}
              className={cn(
                "mt-2 flex items-center gap-1 text-xs font-medium px-3 py-1.5 rounded-lg transition-colors",
                isCompra 
                  ? "bg-green-500/20 text-green-400 hover:bg-green-500/30" 
                  : "bg-red-500/20 text-red-400 hover:bg-red-500/30"
              )}
            >
              VER DETALHES
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>
          
          {/* Fechar */}
          <button
            onClick={() => {
              setSaindo(true)
              setTimeout(() => {
                setVisivel(false)
                marcarLido(ultimoAlerta.id)
              }, 300)
            }}
            className="flex-shrink-0 text-muted-foreground hover:text-foreground transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}