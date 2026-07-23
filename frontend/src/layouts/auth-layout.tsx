import * as React from "react"
import { Outlet } from "react-router-dom"
import { cn } from "@/lib/utils"

interface AuthLayoutProps {
  className?: string
}

export function AuthLayout({ className }: AuthLayoutProps) {
  return (
    <div className={cn("min-h-screen flex items-center justify-center bg-muted/40", className)}>
      <div className="w-full max-w-md p-8">
        <Outlet />
      </div>
    </div>
  )
}
