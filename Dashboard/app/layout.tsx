import type { Metadata, Viewport } from 'next'  // ⭐ IMPORTE Viewport
import { Geist, Geist_Mono } from 'next/font/google'
import './globals.css'
import { ChatBot } from "@/components/apps/ChatBot"

const geist = Geist({ subsets: ["latin"] });
const geistMono = Geist_Mono({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: 'TRADER AI',
  description: 'Sistema de Trading com IA Adaptativa',
  manifest: '/manifest.json',
  // ⭐ REMOVA themeColor DAQUI
}

// ⭐ ADICIONE viewport SEPARADO
export const viewport: Viewport = {
  themeColor: '#0d1a28',
  width: 'device-width',
  initialScale: 1,
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="pt-BR">
      <body className="font-sans antialiased">
        {children}
        <ChatBot /> 
      </body>
      
    </html>
  )
}