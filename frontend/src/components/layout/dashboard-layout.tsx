"use client"

import { useRouter } from "next/navigation"
import { useEffect } from "react"
import { Sidebar } from "@/components/ui/sidebar"
import { PageHeader } from "@/components/ui/page-header"
import { useAuth } from "@/components/providers/auth-provider"
import { LucideIcon } from "lucide-react"

interface DashboardLayoutProps {
  title: string
  showBackButton?: boolean
  backUrl?: string
  backLabel?: string
  actions?: React.ReactNode
  children: React.ReactNode
  icon?: LucideIcon
}

export function DashboardLayout({
  title,
  showBackButton = false,
  backUrl,
  backLabel = "Back",
  actions,
  children,
  icon
}: DashboardLayoutProps) {
  const { loading, isAuthenticated } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (loading) return // Still loading
    if (!isAuthenticated) router.push("/auth/signin") // Not authenticated
  }, [isAuthenticated, loading, router])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return null // Will redirect to sign-in
  }

  return (
    <div className="h-screen bg-gray-50 overflow-hidden">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content */}
      <div className="ml-64 flex flex-col h-screen overflow-hidden">
        {/* Header */}
        <PageHeader 
          title={title}
          showBackButton={showBackButton}
          backUrl={backUrl}
          backLabel={backLabel}
          actions={actions}
          icon={icon}
        />

        {/* Content */}
        <main className="flex-1 p-6 flex flex-col overflow-hidden">
          {children}
        </main>
      </div>
    </div>
  )
}
