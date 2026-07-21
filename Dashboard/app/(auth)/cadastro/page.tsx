"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { TrendingUp, User, Mail, Lock, Loader2, Eye, EyeOff, ArrowRight, Check } from "lucide-react"
import { supabase } from "@/lib/supabase-client"

export default function CadastroPage() {
  const router = useRouter()
  const [nome, setNome] = useState("")
  const [email, setEmail] = useState("")
  const [senha, setSenha] = useState("")
  const [mostrarSenha, setMostrarSenha] = useState(false)
  const [loading, setLoading] = useState(false)
  const [erro, setErro] = useState("")
  const [sucesso, setSucesso] = useState(false)

  async function handleCadastro(e: React.FormEvent) {
    e.preventDefault()
    if (!nome || !email || !senha) return
    
    if (senha.length < 6) {
      setErro("A senha deve ter pelo menos 6 caracteres.")
      return
    }

    setLoading(true)
    setErro("")

    try {
      const { error } = await supabase.auth.signUp({
        email,
        password: senha,
        options: { data: { nome } }
      })
      
      if (error) throw error
      
      setSucesso(true)
      setTimeout(() => {
        router.push("/onboarding")
      }, 2000)
    } catch (err: any) {
      setErro(err.message === "User already registered"
        ? "Este email já está cadastrado."
        : "Erro ao criar conta. Tente novamente.")
    } finally {
      setLoading(false)
    }
  }

  if (sucesso) {
    return (
      <div className="min-h-screen bg-[#060b14] flex items-center justify-center p-4">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-green-500/10 border border-green-500/30 mb-6">
            <Check className="w-10 h-10 text-green-400" />
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">Conta criada!</h1>
          <p className="text-zinc-400">Redirecionando para configuração...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#060b14] flex items-center justify-center p-4 relative overflow-hidden">
      {/* Marca d'água */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-[0.03]">
        <svg width="800" height="800" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg">
          <ellipse cx="256" cy="256" rx="240" ry="55" fill="none" stroke="#06b6d4" strokeWidth="3" transform="rotate(-12, 256, 256)"/>
          <ellipse cx="256" cy="256" rx="220" ry="52" fill="none" stroke="#06b6d4" strokeWidth="3" transform="rotate(-0.85, 256, 256)"/>
          <ellipse cx="256" cy="256" rx="200" ry="48" fill="none" stroke="#06b6d4" strokeWidth="4" transform="rotate(12, 256, 256)"/>
          <ellipse cx="256" cy="256" rx="160" ry="42" fill="none" stroke="#06b6d4" strokeWidth="5" transform="rotate(24.86, 256, 256)"/>
          <ellipse cx="256" cy="256" rx="130" ry="38" fill="none" stroke="#06b6d4" strokeWidth="6" transform="rotate(37.727, 256, 256)"/>
          <ellipse cx="256" cy="256" rx="90" ry="30" fill="none" stroke="#06b6d4" strokeWidth="8" transform="rotate(50.587, 256, 256)"/>
          <ellipse cx="256" cy="256" rx="55" ry="24" fill="none" stroke="#06b6d4" strokeWidth="10" transform="rotate(63.44, 256, 256)"/>
          <circle cx="256" cy="256" r="18" fill="#06b6d4"/>
          <circle cx="256" cy="256" r="9" fill="#22d3ee"/>
          <circle cx="256" cy="256" r="4" fill="#ffffff"/>
        </svg>
      </div>

      <div className="relative w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-500 to-blue-600 mb-4 shadow-lg shadow-cyan-500/20">
            <TrendingUp className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">Trader AI</h1>
          <p className="text-zinc-500 text-sm mt-1">Crie sua conta gratuita</p>
        </div>

        {/* Formulário */}
        <form onSubmit={handleCadastro} className="bg-zinc-900/80 border border-zinc-800 rounded-2xl p-6 shadow-2xl backdrop-blur-sm">
          {erro && (
            <div className="mb-4 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm text-center">
              {erro}
            </div>
          )}

          <div className="space-y-4">
            {/* Nome */}
            <div>
              <label className="text-xs text-zinc-500 mb-1.5 block">Nome</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-600" />
                <input
                  type="text"
                  value={nome}
                  onChange={e => setNome(e.target.value)}
                  placeholder="Seu nome completo"
                  className="w-full bg-zinc-800 border border-zinc-700 rounded-xl pl-10 pr-4 py-3 text-white placeholder:text-zinc-600 focus:outline-none focus:border-cyan-500 transition-colors"
                  required
                />
              </div>
            </div>

            {/* Email */}
            <div>
              <label className="text-xs text-zinc-500 mb-1.5 block">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-600" />
                <input
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="seu@email.com"
                  className="w-full bg-zinc-800 border border-zinc-700 rounded-xl pl-10 pr-4 py-3 text-white placeholder:text-zinc-600 focus:outline-none focus:border-cyan-500 transition-colors"
                  required
                />
              </div>
            </div>

            {/* Senha */}
            <div>
              <label className="text-xs text-zinc-500 mb-1.5 block">Senha</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-600" />
                <input
                  type={mostrarSenha ? "text" : "password"}
                  value={senha}
                  onChange={e => setSenha(e.target.value)}
                  placeholder="Mínimo 6 caracteres"
                  className="w-full bg-zinc-800 border border-zinc-700 rounded-xl pl-10 pr-12 py-3 text-white placeholder:text-zinc-600 focus:outline-none focus:border-cyan-500 transition-colors"
                  required
                />
                <button
                  type="button"
                  onClick={() => setMostrarSenha(!mostrarSenha)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-600 hover:text-zinc-400 transition-colors"
                >
                  {mostrarSenha ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || !nome || !email || !senha}
            className="w-full mt-6 flex items-center justify-center gap-2 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-semibold py-3 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-cyan-500/20"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <>
                Criar conta
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        <p className="text-center text-zinc-600 text-sm mt-6">
          Já tem conta?{" "}
          <Link href="/login" className="text-cyan-400 hover:text-cyan-300 transition-colors font-medium">
            Fazer login
          </Link>
        </p>
      </div>
    </div>
  )
}