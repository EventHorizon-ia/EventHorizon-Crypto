// lib/supabase-client.ts
import { createBrowserClient } from "@supabase/ssr"

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL!
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

// ⭐ Cliente principal
export const supabase = createBrowserClient(SUPABASE_URL, SUPABASE_ANON_KEY)

// ⭐ Função para criar cliente (mantida para compatibilidade)
export function criarClienteNavegador() {
  return supabase
}

// ⭐ Funções de autenticação
export async function getUser() {
  const { data } = await supabase.auth.getUser()
  return data.user
}

export async function login(email: string, password: string) {
  return await supabase.auth.signInWithPassword({ email, password })
}

export async function logout() {
  return await supabase.auth.signOut()
}

export async function signUp(email: string, password: string, nome: string) {
  return await supabase.auth.signUp({
    email,
    password,
    options: { data: { nome } }
  })
}

// ⭐ Função para salvar onboarding (CRUCIAL)
// ⭐ Função para salvar onboarding (CRUCIAL)
export async function salvarOnboarding(
  userId: string,
  respostas: {
    nivel_experiencia: string
    horas_dia: string
    apetite_risco: string
    qtd_moedas: string
    alertas_tipo: string
  }
): Promise<boolean> {
  const { error } = await supabase
    .from("perfis")  // ✅ Mudou de "users" para "perfis"
    .upsert({
      user_id: userId,  // 👈 Mudou de 'id' para 'user_id'
      nivel_experiencia: respostas.nivel_experiencia,
      horas_dia: respostas.horas_dia,
      apetite_risco: respostas.apetite_risco,
      qtd_moedas: respostas.qtd_moedas,
      alertas_tipo: respostas.alertas_tipo,
      onboarding_completo: true,
      plano: 'basico',
      status: 'ativo',
      updated_at: new Date().toISOString()
    })
    .eq("user_id", userId)

  return !error
}