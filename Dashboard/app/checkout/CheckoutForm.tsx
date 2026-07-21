'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { criarClienteNavegador } from "@/lib/supabase-client"
import { Zap, Copy, CheckCircle, ArrowLeft } from "lucide-react"

export function CheckoutForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const planoParam = searchParams.get("plano")

  const [plano, setPlano] = useState<"basico" | "pro" | "enterprise">("pro")
  const [userId, setUserId] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [loading, setLoading] = useState(false)

  const planos = {
    basico: { nome: "Básico", preco: 97, moedas: 3 },
    pro: { nome: "Pro", preco: 197, moedas: 10 },
    enterprise: { nome: "Enterprise", preco: 497, moedas: 20 },
  }

  const planoInfo = planos[plano as keyof typeof planos] || planos.pro
  const chavePix = "seu-email@provedor.com"

  useEffect(() => {
    if (planoParam && planos[planoParam as keyof typeof planos]) {
      setPlano(planoParam as "basico" | "pro" | "enterprise")
    }

    const supabase = criarClienteNavegador()
    supabase.auth.getUser().then(({ data }) => {
      if (data.user) setUserId(data.user.id)
    })
  }, [planoParam])

  async function handlePagar() {
    if (!userId) {
      alert("Usuário não identificado. Faça login novamente.")
      router.push("/login")
      return
    }

    setLoading(true)

    const supabase = criarClienteNavegador()
    await supabase.from("pagamentos").insert({
      user_id: userId,
      valor: planoInfo.preco,
      plano: plano,
      status: "pendente",
      metodo: "pix",
    })

    setLoading(false)
    alert(`Pagamento pendente. Após confirmar o PIX, entre em contato no WhatsApp para ativar seu plano: (seu numero)`)
  }

  async function handlePular() {
    setLoading(true)

    if (userId) {
      const supabase = criarClienteNavegador()
      await supabase
        .from("perfis")
        .update({ plano: "basico", status: "ativo" })
        .eq("user_id", userId)
    }

    router.push("/dashboard")
  }

  function copyPix() {
    navigator.clipboard.writeText(chavePix)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="min-h-screen bg-[#080c14] flex flex-col items-center justify-center p-4">
      {/* Todo o seu JSX permanece igual */}

      <div className="max-w-md w-full">
        <button
          onClick={() => router.back()}
          className="flex items-center gap-2 text-zinc-500 hover:text-zinc-300 mb-6 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Voltar
        </button>

        <div className="bg-zinc-900/80 border border-zinc-800 rounded-2xl p-6">
          {/* ... conteúdo da página ... */}
          <div className="text-center mb-6">
            <div className="w-16 h-16 rounded-full bg-cyan-500/10 flex items-center justify-center mx-auto mb-4">
              <Zap className="w-8 h-8 text-cyan-400" />
            </div>
            <h1 className="text-2xl font-bold text-white">Assinar Plano</h1>
            <p className="text-zinc-400 text-sm mt-1">Escolha a forma de pagamento</p>
          </div>

          {/* Resumo do plano */}
          <div className="bg-zinc-800/50 rounded-xl p-4 mb-6">
            <div className="flex justify-between items-center">
              <div>
                <p className="text-zinc-400 text-sm">Plano selecionado</p>
                <p className="text-xl font-bold text-white">{planoInfo.nome}</p>
              </div>
              <div className="text-right">
                <p className="text-zinc-400 text-sm">Valor</p>
                <p className="text-2xl font-bold text-cyan-400">R$ {planoInfo.preco}</p>
                <p className="text-xs text-zinc-500">/mês</p>
              </div>
            </div>
            <div className="mt-3 pt-3 border-t border-zinc-700">
              <p className="text-sm text-zinc-400">{planoInfo.moedas} moedas monitoradas</p>
              <p className="text-sm text-zinc-400">
                {plano === "pro" && "✓ Alertas no Telegram"}
                {plano === "enterprise" && "✓ Alertas no Telegram + API prioritária"}
              </p>
            </div>
          </div>

          {/* Pagamento via PIX */}
          <div className="border border-cyan-500/30 rounded-xl p-4 mb-6">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
              <span className="text-sm font-medium text-cyan-400">Pagar via PIX</span>
            </div>

            <div className="bg-zinc-800 rounded-lg p-3 mb-4">
              <p className="text-xs text-zinc-500 mb-1">Chave PIX (copia e cola)</p>
              <div className="flex items-center gap-2">
                <code className="flex-1 text-sm text-white font-mono break-all">{chavePix}</code>
                <button onClick={copyPix} className="p-2 rounded-lg bg-zinc-700 hover:bg-zinc-600 transition-colors">
                  {copied ? <CheckCircle className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4 text-zinc-400" />}
                </button>
              </div>
            </div>

            <div className="bg-zinc-800/50 rounded-lg p-3 mb-4">
              <p className="text-xs text-zinc-500 mb-1">Valor a pagar</p>
              <p className="text-xl font-bold text-white">R$ {planoInfo.preco},00</p>
            </div>

            <button
              onClick={handlePagar}
              disabled={loading}
              className="w-full bg-green-500 hover:bg-green-600 text-white font-semibold py-3 rounded-xl transition-colors disabled:opacity-50"
            >
              {loading ? "Processando..." : "Pagar via PIX"}
            </button>

            <p className="text-xs text-zinc-500 text-center mt-3">
              Após o pagamento, você será redirecionado para o dashboard.
              <br />
              <span className="text-cyan-400">💰 Pague e depois confirme no WhatsApp</span>
            </p>
          </div>

          <button
            onClick={handlePular}
            className="w-full text-center text-sm text-zinc-500 hover:text-zinc-400 transition-colors"
          >
            Continuar com o plano Básico gratuito →
          </button>
        </div>
      </div>
    </div>
  );
}