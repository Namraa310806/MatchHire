import * as React from "react"
import { Outlet } from "react-router-dom"
import { cn } from "@/lib/utils"
import { ThemeToggle } from "@/components/theme-toggle"
import { Button } from "@/components/ui/button"
import { Link } from "react-router-dom"

interface PublicLayoutProps {
  className?: string
}

export function PublicLayout({ className }: PublicLayoutProps) {
  return (
    <div className={cn("min-h-screen flex flex-col", className)}>
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <Link to="/" className="text-2xl font-bold">
            MatchHire
          </Link>
          <nav className="flex items-center gap-4">
            <ThemeToggle />
            <Button variant="ghost" asChild>
              <Link to="/login">Login</Link>
            </Button>
            <Button asChild>
              <Link to="/register">Get Started</Link>
            </Button>
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="border-t py-6">
        <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
          © 2024 MatchHire. All rights reserved.
        </div>
      </footer>
    </div>
  )
}
