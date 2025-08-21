"use client"

import { useRouter } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { DashboardLayout } from "@/components/layout/dashboard-layout"
import { RouteGuard } from "@/components/auth/route-guard"
import { Users, Shield, Key, ChevronRight, Settings } from "lucide-react"

const masterItems = [
  {
    title: "Users",
    description: "Manage system users and assignments",
    href: "/masters/users",
    icon: Users,
    bgColor: "bg-blue-100",
    iconColor: "text-blue-600",
  },
  {
    title: "Roles",
    description: "Manage user roles and permissions",
    href: "/masters/roles",
    icon: Shield,
    bgColor: "bg-emerald-100",
    iconColor: "text-emerald-600",
  },
  {
    title: "Permissions",
    description: "Manage system permissions",
    href: "/masters/permissions",
    icon: Key,
    bgColor: "bg-purple-100",
    iconColor: "text-purple-600",
  },
]

export default function Masters() {
  const router = useRouter()

  return (
    <RouteGuard allowedRoles={["Administrator"]}>
      <DashboardLayout title="Masters" icon={Settings}>
        <div className="grid grid-cols-1 gap-4">
          {masterItems.map((item) => {
            const Icon = item.icon

            return (
              <Card 
                key={item.href} 
                className="hover:shadow-md transition-shadow cursor-pointer w-full"
                onClick={() => router.push(item.href)}
              >
                <CardHeader className="gap-0">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className={`p-2 ${item.bgColor} rounded-lg`}>
                        <Icon className={`h-5 w-5 ${item.iconColor}`} />
                      </div>
                      <div>
                        <CardTitle className="text-lg">{item.title}</CardTitle>
                      </div>
                    </div>
                    <ChevronRight className="h-4 w-4 text-muted-foreground" />
                  </div>
                </CardHeader>
              </Card>
            )
          })}
        </div>

        {/* Empty State for Future Items */}
        {masterItems.length === 0 && (
          <div className="mt-8 text-center py-12">
            <div className="text-muted-foreground">
              <p className="text-sm">More master data sections will be available soon.</p>
            </div>
          </div>
        )}
      </DashboardLayout>
    </RouteGuard>
  )
}
