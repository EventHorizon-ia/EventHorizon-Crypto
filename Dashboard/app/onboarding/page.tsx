"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { TrendingUp, ChevronRight, ChevronLeft, Check, User, Mail, Loader2 } from "lucide-react"
import { criarClienteNavegador } from "@/lib/supabase-client"

export default function OnboardingPage() {
  const router = useRouter()
  const supabase = criarClienteNavegador()

  const [etapa, setEtapa] = useState(0)
  const [nome, setNome] = useState("")
  const [email, setEmail] = useState("")
  const [salvando, setSalvando] = useState(false)
  const [userId, setUserId] = useState<string | null>(null)

  useEffect(() => {
    supabase.auth.getUser().then(({ data }) => {
      if (data.user) {
        setUserId(data.user.id)
        setEmail(data.user.email || "")
      }
    })
  }, [supabase])

  async function finalizar() {
    if (!userId || !nome.trim()) return
    setSalvando(true)

    try {
      await supabase
        .from("perfis")
        .upsert({
          user_id: userId,
          nome: nome.trim(),
          onboarding_completo: true,
          plano: "basico",
          updated_at: new Date().toISOString()
        })

      router.push("/dashboard")
      router.refresh()
    } catch (err: any) {
      console.error("Erro ao salvar:", err)
      alert("Erro ao salvar. Tente novamente.")
    } finally {
      setSalvando(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#080c14] flex flex-col items-center justify-center p-4">
      <div className="relative w-full max-w-md">
        {/* Logo */}
        <div className="flex items-center justify-center gap-2 mb-8">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-400 to-blue-600">
            <TrendingUp className="w-4 h-4 text-white" />
          </div>
          <span className="text-sm font-bold text-white tracking-tight">TRADER AI</span>
        </div>

        {/* Progresso */}
        <div className="mb-8">
          <div className="flex items-center justify-between text-xs text-zinc-500 mb-2">
            <span>Configurando seu perfil</span>
            <span>Etapa {etapa + 1} de 2</span>
          </div>
          <div className="h-1 bg-zinc-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-cyan-500 to-blue-600 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${((etapa + 1) / 2) * 100}%` }}
            />
          </div>
        </div>

        {/* Etapa 1: Nome */}
        {etapa === 0 && (
          <div className="bg-zinc-900/80 border border-zinc-800 rounded-2xl p-8 shadow-2xl">
            <div className="flex items-center gap-3 mb-6">
              <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20">
                <User className="w-5 h-5 text-cyan-400" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-white">Como devemos te chamar?</h2>
                <p className="text-sm text-zinc-400">Seu nome ou apelido</p>
              </div>
            </div>

            <input
              type="text"
              value={nome}
              onChange={e => setNome(e.target.value)}
              placeholder="Ex: Lucas"
              className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-4 py-3 text-white placeholder:text-zinc-500 focus:outline-none focus:border-cyan-500 transition-colors"
              autoFocus
              onKeyDown={e => { if (e.key === "Enter" && nome.trim()) setEtapa(1) }}
            />

            <button
              onClick={() => setEtapa(1)}
              disabled={!nome.trim()}
              className="w-full mt-4 flex items-center justify-center gap-2 bg-cyan-500 hover:bg-cyan-400 text-white font-semibold py-3 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Continuar
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Etapa 2: Confirmação */}
        {etapa === 1 && (
          <div className="bg-zinc-900/80 border border-zinc-800 rounded-2xl p-8 shadow-2xl">
            <div className="flex items-center gap-3 mb-6">
              <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20">
                <Mail className="w-5 h-5 text-cyan-400" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-white">Confirme seus dados</h2>
                <p className="text-sm text-zinc-400">Você pode editar depois</p>
              </div>
            </div>

            <div className="space-y-3 mb-6">
              <div className="bg-zinc-800/50 rounded-xl p-4">
                <p className="text-xs text-zinc-500">Nome</p>
                <p className="text-white font-medium">{nome}</p>
              </div>
              <div className="bg-zinc-800/50 rounded-xl p-4">
                <p className="text-xs text-zinc-500">Email</p>
                <p className="text-white font-medium">{email}</p>
              </div>
            </div>

            <div className="space-y-3">
              <button
                onClick={finalizar}
                disabled={salvando}
                className="w-full flex items-center justify-center gap-2 bg-cyan-500 hover:bg-cyan-400 text-white font-semibold py-3 rounded-xl transition-all"
              >
                {salvando ? (
                  <><Loader2 className="w-4 h-4 animate-spin" /> Salvando...</>
                ) : (
                  <>Começar a usar o Trader AI</>
                )}
              </button>

              <button
                onClick={() => setEtapa(0)}
                className="w-full flex items-center justify-center gap-2 text-zinc-500 hover:text-zinc-300 text-sm py-2 transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
                Voltar
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}