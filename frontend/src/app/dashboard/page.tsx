"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { DashboardLayout } from "@/components/layout/dashboard-layout"
import { LogOut, User, Mail, Calendar, LayoutDashboard, Clock, AlertCircle, Users, CheckCircle, XCircle } from "lucide-react"
import { useAuth } from "@/components/providers/auth-provider"
import { useRouter } from "next/navigation"
import { toast } from "sonner"

interface PendingTeacher {
  id: string
  name: string
  email: string
  requested_role_name: string
  created_at: string
  approval_status: string
}

export default function Dashboard() {
  const { user, logout } = useAuth()
  const router = useRouter()
  const [pendingTeachers, setPendingTeachers] = useState<PendingTeacher[]>([])
  const [loadingPending, setLoadingPending] = useState(false)
  const [approving, setApproving] = useState<string | null>(null)

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

  // Fetch pending teachers for administrators
  const fetchPendingTeachers = async () => {
    if (user?.role_name !== "Administrator") return
    
    try {
      setLoadingPending(true)
      const token = localStorage.getItem('auth_token')
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/auth/pending-teachers`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })

      if (response.ok) {
        const data = await response.json()
        setPendingTeachers(data.pending_teachers || [])
      }
    } catch (err) {
      console.error('Error fetching pending teachers:', err)
    } finally {
      setLoadingPending(false)
    }
  }

  // Handle teacher approval/rejection
  const handleTeacherAction = async (teacherId: string, action: 'approve' | 'reject') => {
    try {
      setApproving(teacherId)
      const token = localStorage.getItem('auth_token')
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/auth/approve-teacher/${teacherId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action,
          reason: `Teacher account ${action}d from dashboard by administrator`
        })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `Failed to ${action} teacher`)
      }

      const result = await response.json()
      toast.success(result.message)
      
      // Refresh the pending teachers list
      await fetchPendingTeachers()
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred'
      toast.error(`Failed to ${action} teacher`, {
        description: errorMessage,
      })
    } finally {
      setApproving(null)
    }
  }

  useEffect(() => {
    if (user?.role_name === "Administrator") {
      fetchPendingTeachers()
    }
  }, [user])

  return (
    <DashboardLayout title="Dashboard" icon={LayoutDashboard}>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Welcome Card */}
        <Card className="col-span-full">
          <CardHeader>
            <CardTitle className="text-2xl">Welcome back, {user?.name}!</CardTitle>
            <CardDescription>
              You have successfully signed in to your dashboard.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">
              This is your personal dashboard where you can manage your account and access various features.
            </p>
          </CardContent>
        </Card>

        {/* Teacher Approval Status Card */}
        {user && user.role_name === "Teacher" && user.approval_status === "pending" && (
          <Card className="col-span-full border-yellow-200 bg-yellow-50">
            <CardHeader>
              <CardTitle className="flex items-center text-yellow-800">
                <Clock className="h-5 w-5 mr-2" />
                Account Pending Approval
              </CardTitle>
              <CardDescription className="text-yellow-700">
                Your Teacher account is awaiting admin approval
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-start space-x-3">
                <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5" />
                <div className="space-y-2">
                  <p className="text-yellow-800 font-medium">
                    Your Teacher account has been created successfully and is pending admin approval.
                  </p>
                  <p className="text-yellow-700 text-sm">
                    You will receive an email notification once your account is approved. In the meantime, you can view your profile information but access to teaching features like Courses and Masters is limited.
                  </p>
                  <div className="mt-4 p-3 bg-yellow-100 rounded-md">
                    <p className="text-xs text-yellow-800">
                      <strong>What happens next?</strong><br />
                      • An administrator will review your Teacher account request<br />
                      • You'll receive an email notification with the approval decision<br />
                      • Once approved, you'll have full access to all teaching features including Courses and Masters
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Pending Teacher Approvals Card for Administrators */}
        {user?.role_name === "Administrator" && pendingTeachers.length > 0 && (
          <Card className="col-span-full border-amber-200 bg-amber-50">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <AlertCircle className="h-5 w-5 text-amber-600" />
                  <CardTitle className="text-amber-800">Pending Teacher Approvals</CardTitle>
                </div>
                <Badge variant="outline" className="bg-amber-100 text-amber-800 border-amber-300">
                  {pendingTeachers.length} pending
                </Badge>
              </div>
              <CardDescription className="text-amber-700">
                Review and approve teacher account requests
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {pendingTeachers.slice(0, 3).map((teacher) => (
                  <div key={teacher.id} className="flex items-center justify-between p-3 bg-white rounded-lg border border-amber-200">
                    <div className="flex items-center space-x-3">
                      <Avatar className="h-8 w-8">
                        <AvatarFallback className="bg-amber-100 text-amber-700">
                          {getInitials(teacher.name)}
                        </AvatarFallback>
                      </Avatar>
                      <div>
                        <p className="font-medium text-gray-900">{teacher.name}</p>
                        <p className="text-sm text-gray-600">{teacher.email}</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-green-600 hover:text-green-700 hover:bg-green-50 border-green-200"
                        onClick={() => handleTeacherAction(teacher.id, 'approve')}
                        disabled={approving === teacher.id}
                      >
                        {approving === teacher.id ? (
                          <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-green-600"></div>
                        ) : (
                          <CheckCircle className="h-3 w-3" />
                        )}
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-red-600 hover:text-red-700 hover:bg-red-50 border-red-200"
                        onClick={() => handleTeacherAction(teacher.id, 'reject')}
                        disabled={approving === teacher.id}
                      >
                        {approving === teacher.id ? (
                          <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-red-600"></div>
                        ) : (
                          <XCircle className="h-3 w-3" />
                        )}
                      </Button>
                    </div>
                  </div>
                ))}
                {pendingTeachers.length > 3 && (
                  <div className="text-center pt-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => router.push('/masters/users')}
                      className="text-amber-700 hover:text-amber-800 border-amber-300"
                    >
                      View all {pendingTeachers.length} pending approvals
                    </Button>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* User Info Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <User className="h-5 w-5 mr-2" />
              Profile Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center space-x-3">
              <Avatar className="h-12 w-12">
                <AvatarImage src={user?.avatar || ""} alt={user?.name || ""} />
                <AvatarFallback>
                  {user?.name ? getInitials(user.name) : "U"}
                </AvatarFallback>
              </Avatar>
              <div>
                <p className="font-medium">{user?.name || "No name provided"}</p>
                <p className="text-sm text-muted-foreground">User</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Mail className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm">{user?.email}</span>
            </div>
          </CardContent>
        </Card>

        {/* Session Info Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Calendar className="h-5 w-5 mr-2" />
              Session Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div>
              <p className="text-sm font-medium">Authentication Method</p>
              <p className="text-sm text-muted-foreground">
                {user?.google_id ? "Google OAuth" : "Email & Password"}
              </p>
            </div>
            <div>
              <p className="text-sm font-medium">Session Status</p>
              <p className="text-sm text-green-600">Active</p>
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions Card */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>
              Common tasks and features
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <Button variant="outline" className="w-full justify-start">
              <User className="h-4 w-4 mr-2" />
              Edit Profile
            </Button>
            <Button variant="outline" className="w-full justify-start">
              <Mail className="h-4 w-4 mr-2" />
              Change Email
            </Button>
            <Button variant="outline" className="w-full justify-start" onClick={handleSignOut}>
              <LogOut className="h-4 w-4 mr-2" />
              Sign Out
            </Button>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}
