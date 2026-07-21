"use client"

import { Terminal } from "@/components/terminal/terminal"

interface TerminalTabProps {
  isConnected: boolean
  onExecuteCommand: (command: string) => Promise<string>
}

export function TerminalTab({ isConnected, onExecuteCommand }: TerminalTabProps) {
  return (
    <div className="h-[calc(100vh-220px)] min-h-[400px]">
      <Terminal
        isConnected={isConnected}
        onExecuteCommand={onExecuteCommand}
      />
    </div>
  )
}
