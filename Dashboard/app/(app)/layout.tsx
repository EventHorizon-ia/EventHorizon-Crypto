// app/layout.tsx (OU onde está seu RootLayout)
"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { Sidebar } from "@/components/Sidebar"
import { supabase, getUser } from "@/lib/supabase-client"
import { AlertasProvider } from "@/contexts/AlertasContext"  // ⭐ NOVO
import { AlertasToast } from "@/components/AlertasToast"      // ⭐ NOVO

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [usuario, setUsuario] = useState<any>(null)

  useEffect(() => {
    const verificarAuth = async () => {
      const user = await getUser()

      if (!user) {
        router.replace("/login")
        return
      }

      const { data: perfil, error } = await supabase
        .from("perfis")
        .select("*")
        .eq("user_id", user.id)
        .single()

      if (error) {
        router.replace("/login")
        return
      }

      setUsuario(perfil)
      setLoading(false)
    }

    verificarAuth()
  }, [router])

  if (loading) {
    return (
      <div className="min-h-screen bg-[#080c14] flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-cyan-500 border-t-transparent" />
      </div>
    )
  }

  return (
    <AlertasProvider>  {/* ⭐ ENVOLVE TUDO */}
      <div className="flex min-h-screen bg-[#080c14]">
        <Sidebar usuario={usuario} />
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </div>
      <AlertasToast />  {/* ⭐ TOAST GLOBAL */}
    </AlertasProvider>
  )
}