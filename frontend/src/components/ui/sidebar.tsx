"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { LayoutDashboard, Settings, LogOut, BookOpen } from "lucide-react"
import { useAuth } from "@/components/providers/auth-provider"
import { useRouter } from "next/navigation"

interface SidebarItem {
  title: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  requiresApproval?: boolean
  allowedRoles?: string[]
}

const sidebarItems: SidebarItem[] = [
  {
    title: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    title: "Courses",
    href: "/courses",
    icon: BookOpen,
    requiresApproval: true, // Requires approval for teachers, always available for students and administrators
    allowedRoles: ["Teacher", "Student", "Administrator"], // Teachers, students, and administrators can access
  },
  {
    title: "Masters",
    href: "/masters",
    icon: Settings,
    allowedRoles: ["Administrator"], // Only administrators can access
  },
]

export function Sidebar() {
  const pathname = usePathname()
  const { user, logout } = useAuth()
  const router = useRouter()

  // Helper function to check if user can access a menu item
  const canAccessMenuItem = (item: SidebarItem) => {
    // Dashboard is always accessible
    if (item.title === "Dashboard") return true;
    
    // Check role-based access first
    if (item.allowedRoles && user?.role_name) {
      if (!item.allowedRoles.includes(user.role_name)) {
        return false; // User's role is not in allowed roles
      }
    }
    
    // For items that require approval (like Courses for Teachers)
    if (item.requiresApproval && user?.role_name === "Teacher") {
      // Only allow access if teacher is approved (not pending)
      return user?.approval_status !== "pending";
    }
    
    return true;
  }

  const handleSignOut = async () => {
    await logout()
    router.push("/auth/signin")
  }

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
  }

  return (
    <div className="flex h-screen w-64 flex-col bg-white fixed left-0 top-0">
      {/* Logo/Brand Section */}
      <div className="flex h-16 items-center px-6 sidebar-border-fix">
        <img src="/Edura_club.svg" alt="Edura" className="h-8 w-auto" />
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 border-r border-border">
        <div className="space-y-3">
          {sidebarItems
            .filter(canAccessMenuItem)
            .map((item) => {
              const isActive = pathname === item.href || pathname.startsWith(item.href + "/")
              const Icon = item.icon

              return (
                <Link key={item.href} href={item.href}>
                  <div
                    className={cn(
                      "flex items-center space-x-3 px-3 py-3 rounded-lg text-gray-700 hover:bg-gray-100 hover:shadow-sm transition-all duration-200 cursor-pointer mb-2",
                      isActive && "bg-gray-100 text-gray-900 font-medium shadow-sm"
                    )}
                  >
                    <Icon className="h-5 w-5" />
                    <span className="text-sm font-medium">{item.title}</span>
                  </div>
                </Link>
              )
            })}
        </div>
      </nav>

      {/* User Profile Section */}
      <div className="border-t border-r border-border p-4">
        <div className="flex items-center space-x-3 mb-4">
          <Avatar className="h-10 w-10">
            <AvatarImage src={user?.avatar || ""} alt={user?.name || ""} />
            <AvatarFallback className="bg-gray-200">
              {user?.name ? getInitials(user.name) : "U"}
            </AvatarFallback>
          </Avatar>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">
              {user?.name || "User"}
            </p>
            <p className="text-xs text-gray-500 truncate">
              {user?.email}
            </p>
          </div>
        </div>
        
        <Button
          variant="outline"
          className="w-full justify-start text-gray-700 hover:text-gray-900"
          onClick={handleSignOut}
        >
          <LogOut className="h-4 w-4 mr-2" />
          Logout
        </Button>
      </div>
    </div>
  )
}
