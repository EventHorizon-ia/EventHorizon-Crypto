"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { getUser } from "@/lib/supabase-client"

export default function HomePage() {
  const router = useRouter()

  useEffect(() => {
    const verificarAuth = async () => {
      const user = await getUser()
      if (user) {
        router.replace("/dashboard")
      } else {
        router.replace("/login")
      }
    }
    verificarAuth()
  }, [router])

  return (
    <div className="min-h-screen bg-[#080c14] flex items-center justify-center">
      <div className="animate-spin rounded-full h-8 w-8 border-2 border-cyan-500 border-t-transparent" />
    </div>
  )
}