"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { criarClienteNavegador } from "@/lib/supabase-client"

export default function RootPage() {
  const router = useRouter()

  useEffect(() => {
    const verificar = async () => {
      const supabase = criarClienteNavegador()
      const { data } = await supabase.auth.getUser()

      if (data.user) {
        router.push("/dashboard")
      } else {
        router.push("/login")
      }
    }
    verificar()
  }, [router])

  return (
    <div className="min-h-screen bg-[#080c14] flex items-center justify-center">
      <div className="animate-spin rounded-full h-8 w-8 border-2 border-cyan-500 border-t-transparent" />
    </div>
  )
}