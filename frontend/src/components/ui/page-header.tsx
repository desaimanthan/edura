"use client"

import { Button } from "@/components/ui/button"
import { ArrowLeft } from "lucide-react"
import { useRouter } from "next/navigation"
import { LucideIcon } from "lucide-react"

interface PageHeaderProps {
  title: string
  showBackButton?: boolean
  backUrl?: string
  backLabel?: string
  actions?: React.ReactNode
  icon?: LucideIcon
}

export function PageHeader({ 
  title, 
  showBackButton = false, 
  backUrl, 
  backLabel = "Back",
  actions,
  icon: Icon
}: PageHeaderProps) {
  const router = useRouter()

  const handleBack = () => {
    if (backUrl) {
      router.push(backUrl)
    } else {
      router.back()
    }
  }

  return (
    <header className="bg-white border-b border-border h-16">
      <div className="px-6 h-full flex items-center justify-between w-full">
        <div className="flex items-center space-x-4">
          {showBackButton && (
            <ArrowLeft 
              className="h-6 w-6 text-gray-600 cursor-pointer hover:text-gray-800 transition-colors" 
              onClick={handleBack}
            />
          )}
          {!showBackButton && Icon && (
            <Icon className="h-6 w-6 text-gray-600" />
          )}
          <h1 className="text-xl font-semibold text-gray-900">{title}</h1>
        </div>
        {actions && (
          <div className="flex items-center space-x-2">
            {actions}
          </div>
        )}
      </div>
    </header>
  )
}
