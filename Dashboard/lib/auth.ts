// lib/auth.ts
// ⭐ APENAS CLIENT COMPONENT (sem next/headers)

"use client"

import { criarClienteNavegador } from "@/lib/supabase-client"

export async function login(email: string, senha: string) {
  const supabase = criarClienteNavegador()
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password: senha,
  })
  return { data, error }
}

export async function cadastro(email: string, senha: string, nome: string) {
  const supabase = criarClienteNavegador()
  const { data, error } = await supabase.auth.signUp({
    email,
    password: senha,
    options: {
      data: { nome },
    },
  })
  return { data, error }
}

export async function logout() {
  const supabase = criarClienteNavegador()
  await supabase.auth.signOut()
  localStorage.removeItem("supabase.auth.token")
}

export async function getUser() {
  const supabase = criarClienteNavegador()
  const { data } = await supabase.auth.getUser()
  return data.user
}