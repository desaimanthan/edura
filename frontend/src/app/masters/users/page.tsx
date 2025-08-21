"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { DashboardLayout } from "@/components/layout/dashboard-layout"
import { RouteGuard } from "@/components/auth/route-guard"
import { Plus, Users, Shield, Edit, Trash2, X, Save, Mail, Calendar, UserCheck, ArrowUpDown, Clock, CheckCircle, XCircle, AlertCircle } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { toast } from "sonner"
import { Textarea } from "@/components/ui/textarea"

// Types
interface Role {
  id?: string
  _id?: string
  name: string
  description: string
}

interface User {
  id?: string
  _id?: string
  email: string
  name: string
  role_id: string
  role: Role
  is_active: boolean
  created_at: string
  updated_at: string
  approval_status?: string
  requested_role_name?: string
}

interface PendingTeacher {
  id: string
  name: string
  email: string
  requested_role_name: string
  created_at: string
  approval_status: string
}

export default function UsersManagement() {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [allRoles, setAllRoles] = useState<Role[]>([])
  
  // Pending teachers state
  const [pendingTeachers, setPendingTeachers] = useState<PendingTeacher[]>([])
  const [pendingLoading, setPendingLoading] = useState(false)
  const [approvalDrawerOpen, setApprovalDrawerOpen] = useState(false)
  const [selectedTeacher, setSelectedTeacher] = useState<PendingTeacher | null>(null)
  const [approvalReason, setApprovalReason] = useState('')
  const [approving, setApproving] = useState(false)
  
  // Edit drawer state
  const [isEditDrawerOpen, setIsEditDrawerOpen] = useState(false)
  const [editingUser, setEditingUser] = useState<User | null>(null)
  const [editForm, setEditForm] = useState({
    name: '',
    email: '',
    role_id: '',
    is_active: true
  })
  const [saving, setSaving] = useState(false)

  // Add user drawer state
  const [isAddDrawerOpen, setIsAddDrawerOpen] = useState(false)
  const [addForm, setAddForm] = useState({
    name: '',
    email: '',
    password: '',
    role_id: '',
    is_active: true
  })
  const [adding, setAdding] = useState(false)

  // Sorting state
  const [sortField, setSortField] = useState<keyof User | 'role_name'>('name')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc')

  // Helper function to get ID from either id or _id field
  const getId = (item: User | Role): string => {
    return item.id || item._id || Math.random().toString(36).substr(2, 9)
  }

  // Helper function to get role badge color based on role name
  const getRoleBadgeColor = (roleName: string): string => {
    const roleNameLower = roleName.toLowerCase()
    
    // Administrator roles - purple
    if (roleNameLower.includes('admin') || roleNameLower.includes('administrator')) {
      return 'bg-purple-100 text-purple-800 border-purple-200'
    }
    
    // Teacher roles - blue
    if (roleNameLower.includes('teacher') || roleNameLower.includes('instructor') || roleNameLower.includes('faculty')) {
      return 'bg-blue-100 text-blue-800 border-blue-200'
    }
    
    // Student roles - orange
    if (roleNameLower.includes('student') || roleNameLower.includes('learner')) {
      return 'bg-orange-100 text-orange-800 border-orange-200'
    }
    
    // Default - slate
    return 'bg-slate-100 text-slate-800 border-slate-200'
  }

  // Fetch all roles for the edit form
  const fetchAllRoles = async () => {
    try {
      const token = localStorage.getItem('auth_token')
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/masters/roles/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })

      if (response.ok) {
        const data = await response.json()
        setAllRoles(data)
      }
    } catch (err) {
      console.error('Error fetching roles:', err)
    }
  }

  // Handle edit user
  const handleEditUser = (user: User) => {
    setEditingUser(user)
    setEditForm({
      name: user.name,
      email: user.email,
      role_id: user.role_id,
      is_active: user.is_active
    })
    setIsEditDrawerOpen(true)
  }

  // Handle save user
  const handleSaveUser = async () => {
    if (!editingUser) return

    try {
      setSaving(true)
      const token = localStorage.getItem('auth_token')
      const userId = getId(editingUser)
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/users/${userId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(editForm)
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to update user')
      }

      // Get the updated user data from the response
      const updatedUser = await response.json()
      
      // Update the local state with the new user data
      setUsers(prevUsers => 
        prevUsers.map(user => 
          getId(user) === getId(editingUser) ? updatedUser : user
        )
      )
      
      setIsEditDrawerOpen(false)
      setEditingUser(null)
      toast.success(`User "${editForm.name}" has been updated successfully.`)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred'
      toast.error("Failed to update user", {
        description: errorMessage,
      })
      console.error('Error updating user:', err)
    } finally {
      setSaving(false)
    }
  }

  // Handle add new user
  const handleAddUser = () => {
    setAddForm({
      name: '',
      email: '',
      password: '',
      role_id: '',
      is_active: true
    })
    setIsAddDrawerOpen(true)
  }

  // Handle save new user
  const handleSaveNewUser = async () => {
    try {
      setAdding(true)
      const token = localStorage.getItem('auth_token')
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/users/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(addForm)
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to create user')
      }

      // Refresh the users list to include the new user
      await fetchUsers()
      
      setIsAddDrawerOpen(false)
      setAddForm({
        name: '',
        email: '',
        password: '',
        role_id: '',
        is_active: true
      })
      toast.success(`User "${addForm.name}" has been created successfully.`)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred'
      toast.error("Failed to create user", {
        description: errorMessage,
      })
      console.error('Error creating user:', err)
    } finally {
      setAdding(false)
    }
  }

  // Handle delete user
  const handleDeleteUser = async (user: User) => {
    const userId = getId(user)
    const confirmDelete = window.confirm(
      `Are you sure you want to delete the user "${user.name}"?\n\n` +
      `Email: ${user.email}\n` +
      `Role: ${user.role.name}\n\n` +
      `This action cannot be undone.`
    )
    
    if (!confirmDelete) return

    try {
      const token = localStorage.getItem('auth_token')
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/users/${userId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to delete user')
      }

      // Refresh the users list
      await fetchUsers()
      toast.success(`User "${user.name}" has been deleted successfully.`)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred'
      toast.error("Failed to delete user", {
        description: errorMessage,
      })
      console.error('Error deleting user:', err)
    }
  }

  // Fetch users from API
  const fetchUsers = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('auth_token')
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/users/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error('Failed to fetch users')
      }

      const data = await response.json()
      setUsers(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
      console.error('Error fetching users:', err)
    } finally {
      setLoading(false)
    }
  }

  // Fetch pending teachers
  const fetchPendingTeachers = async () => {
    try {
      setPendingLoading(true)
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
      setPendingLoading(false)
    }
  }

  // Handle teacher approval
  const handleTeacherApproval = (teacher: PendingTeacher, action: 'approve' | 'reject') => {
    setSelectedTeacher(teacher)
    setApprovalReason('')
    setApprovalDrawerOpen(true)
  }

  // Submit teacher approval
  const submitTeacherApproval = async (action: 'approve' | 'reject') => {
    if (!selectedTeacher) return

    try {
      setApproving(true)
      const token = localStorage.getItem('auth_token')
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/auth/approve-teacher/${selectedTeacher.id}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action,
          reason: approvalReason.trim() || `Teacher account ${action}d by administrator`
        })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `Failed to ${action} teacher`)
      }

      const result = await response.json()
      
      // Refresh both lists
      await Promise.all([fetchUsers(), fetchPendingTeachers()])
      
      setApprovalDrawerOpen(false)
      setSelectedTeacher(null)
      setApprovalReason('')
      
      toast.success(result.message)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred'
      toast.error(`Failed to ${action} teacher`, {
        description: errorMessage,
      })
      console.error(`Error ${action}ing teacher:`, err)
    } finally {
      setApproving(false)
    }
  }

  useEffect(() => {
    fetchUsers()
    fetchAllRoles()
    fetchPendingTeachers()
  }, [])

  // Handle sorting
  const handleSort = (field: keyof User | 'role_name') => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
  }

  // Sort users
  const sortedUsers = [...users].sort((a, b) => {
    let aValue: string | boolean | Date
    let bValue: string | boolean | Date

    switch (sortField) {
      case 'role_name':
        aValue = a.role.name.toLowerCase()
        bValue = b.role.name.toLowerCase()
        break
      case 'created_at':
        aValue = new Date(a.created_at)
        bValue = new Date(b.created_at)
        break
      case 'is_active':
        aValue = a.is_active
        bValue = b.is_active
        break
      default:
        aValue = String(a[sortField]).toLowerCase()
        bValue = String(b[sortField]).toLowerCase()
    }

    if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1
    if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1
    return 0
  })

  // Calculate stats
  const activeUsers = users.filter(user => user.is_active).length
  const inactiveUsers = users.filter(user => !user.is_active).length
  const roleDistribution = users.reduce((acc, user) => {
    const roleName = user.role.name
    acc[roleName] = (acc[roleName] || 0) + 1
    return acc
  }, {} as Record<string, number>)
  const mostCommonRole = Object.entries(roleDistribution).reduce((a, b) => 
    roleDistribution[a[0]] > roleDistribution[b[0]] ? a : b, ['', 0]
  )[0] || 'N/A'

  if (loading) {
    return (
      <DashboardLayout 
        title="Users Management" 
        showBackButton={true}
        backUrl="/masters"
        backLabel="Back to Masters"
      >
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
            <p className="mt-2 text-sm text-muted-foreground">Loading users...</p>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  if (error) {
    return (
      <DashboardLayout 
        title="Users Management" 
        showBackButton={true}
        backUrl="/masters"
        backLabel="Back to Masters"
      >
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <p className="text-red-600">Error: {error}</p>
            <Button onClick={fetchUsers} className="mt-4">
              Try Again
            </Button>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <RouteGuard allowedRoles={["Administrator"]}>
      <DashboardLayout 
        title="Users Management" 
        showBackButton={true}
        backUrl="/masters"
        backLabel="Back to Masters"
        actions={
          <Button className="flex items-center" onClick={handleAddUser}>
            <Plus className="h-4 w-4 mr-2" />
            Add New User
          </Button>
        }
      >
      <>
        {/* Stats Cards */}
        <div key="stats-section" className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          {[
            {
              key: "total-users",
              title: "Total Users",
              value: users.length,
              description: "All users in system",
              icon: Users
            },
            {
              key: "active-users", 
              title: "Active Users",
              value: activeUsers,
              description: "Currently active users",
              icon: UserCheck
            },
            {
              key: "inactive-users",
              title: "Inactive Users", 
              value: inactiveUsers,
              description: "Deactivated users",
              icon: Users
            },
            {
              key: "common-role",
              title: "Most Common Role", 
              value: mostCommonRole,
              description: `${roleDistribution[mostCommonRole] || 0} users`,
              icon: Shield
            }
          ].map((stat) => {
            const Icon = stat.icon
            return (
              <Card key={stat.key}>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
                  <Icon className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stat.value}</div>
                  <p className="text-xs text-muted-foreground">{stat.description}</p>
                </CardContent>
              </Card>
            )
          })}
        </div>

        {/* Pending Teacher Approvals */}
        {pendingTeachers.length > 0 && (
          <Card key="pending-teachers-section" className="mb-8">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <AlertCircle className="h-5 w-5 text-amber-500" />
                  <CardTitle className="text-lg font-semibold">Pending Teacher Approvals</CardTitle>
                </div>
                <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200">
                  {pendingTeachers.length} pending
                </Badge>
              </div>
              <CardDescription>
                Review and approve teacher account requests
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>
                        <div className="flex items-center space-x-2">
                          <Mail className="h-4 w-4 text-muted-foreground" />
                          <span>Email</span>
                        </div>
                      </TableHead>
                      <TableHead>
                        <div className="flex items-center space-x-2">
                          <Shield className="h-4 w-4 text-muted-foreground" />
                          <span>Requested Role</span>
                        </div>
                      </TableHead>
                      <TableHead>
                        <div className="flex items-center space-x-2">
                          <Clock className="h-4 w-4 text-muted-foreground" />
                          <span>Status</span>
                        </div>
                      </TableHead>
                      <TableHead>
                        <div className="flex items-center space-x-2">
                          <Calendar className="h-4 w-4 text-muted-foreground" />
                          <span>Requested</span>
                        </div>
                      </TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {pendingTeachers.map((teacher) => (
                      <TableRow key={teacher.id}>
                        <TableCell>
                          <div className="font-medium">{teacher.name}</div>
                        </TableCell>
                        <TableCell>
                          <span>{teacher.email}</span>
                        </TableCell>
                        <TableCell>
                          <Badge 
                            variant="outline" 
                            className="text-xs bg-blue-100 text-blue-800 border-blue-200"
                          >
                            {teacher.requested_role_name}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge 
                            variant="outline"
                            className="text-xs bg-amber-100 text-amber-800 border-amber-200"
                          >
                            <Clock className="h-3 w-3 mr-1" />
                            Pending
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <span className="text-sm">
                            {new Date(teacher.created_at).toLocaleDateString()}
                          </span>
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex items-center justify-end space-x-2">
                            <Button 
                              variant="outline" 
                              size="sm"
                              className="text-green-600 hover:text-green-700 hover:bg-green-50"
                              onClick={() => handleTeacherApproval(teacher, 'approve')}
                            >
                              <CheckCircle className="h-4 w-4 mr-1" />
                              Approve
                            </Button>
                            <Button 
                              variant="outline" 
                              size="sm" 
                              className="text-red-600 hover:text-red-700 hover:bg-red-50"
                              onClick={() => handleTeacherApproval(teacher, 'reject')}
                            >
                              <XCircle className="h-4 w-4 mr-1" />
                              Reject
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Users Table */}
        <Card key="users-section">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg font-semibold">All Users</CardTitle>
              <div className="text-sm text-muted-foreground">
                {users.length} user{users.length !== 1 ? 's' : ''} total
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead 
                      sortable 
                      sortDirection={sortField === 'name' ? sortDirection : null}
                      onSort={() => handleSort('name')}
                    >
                      Name
                    </TableHead>
                    <TableHead 
                      sortable 
                      sortDirection={sortField === 'email' ? sortDirection : null}
                      onSort={() => handleSort('email')}
                    >
                      <div className="flex items-center space-x-2">
                        <Mail className="h-4 w-4 text-muted-foreground" />
                        <span>Email</span>
                      </div>
                    </TableHead>
                    <TableHead 
                      sortable 
                      sortDirection={sortField === 'role_name' ? sortDirection : null}
                      onSort={() => handleSort('role_name')}
                    >
                      <div className="flex items-center space-x-2">
                        <Shield className="h-4 w-4 text-muted-foreground" />
                        <span>Role</span>
                      </div>
                    </TableHead>
                    <TableHead 
                      sortable 
                      sortDirection={sortField === 'is_active' ? sortDirection : null}
                      onSort={() => handleSort('is_active')}
                    >
                      <div className="flex items-center space-x-2">
                        <UserCheck className="h-4 w-4 text-muted-foreground" />
                        <span>Status</span>
                      </div>
                    </TableHead>
                    <TableHead 
                      sortable 
                      sortDirection={sortField === 'created_at' ? sortDirection : null}
                      onSort={() => handleSort('created_at')}
                    >
                      <div className="flex items-center space-x-2">
                        <Calendar className="h-4 w-4 text-muted-foreground" />
                        <span>Joined</span>
                      </div>
                    </TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sortedUsers.map((user) => {
                    const userId = getId(user)
                    return (
                      <TableRow key={userId}>
                        <TableCell>
                          <div className="font-medium">{user.name}</div>
                        </TableCell>
                        <TableCell>
                          <span>{user.email}</span>
                        </TableCell>
                        <TableCell>
                          <Badge 
                            variant="outline" 
                            className={`text-xs ${getRoleBadgeColor(user.role.name)}`}
                          >
                            {user.role.name}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge 
                            variant="outline"
                            className={`text-xs ${
                              user.is_active 
                                ? 'bg-green-100 text-green-800 border-green-200' 
                                : 'bg-red-100 text-red-800 border-red-200'
                            }`}
                          >
                            {user.is_active ? 'Active' : 'Inactive'}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <span className="text-sm">
                            {new Date(user.created_at).toLocaleDateString()}
                          </span>
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex items-center space-x-2">
                            <Button 
                              variant="outline" 
                              size="sm"
                              onClick={() => handleEditUser(user)}
                            >
                              <Edit className="h-4 w-4 mr-1" />
                              Edit
                            </Button>
                            <Button 
                              variant="outline" 
                              size="sm" 
                              className="text-destructive hover:text-destructive"
                              onClick={() => handleDeleteUser(user)}
                            >
                              <Trash2 className="h-4 w-4 mr-1" />
                              Delete
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>

        {/* Empty State */}
        {users.length === 0 && (
          <div key="empty-state" className="text-center py-12">
            <Users className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">No users found</h3>
            <p className="text-muted-foreground mb-4">
              Get started by adding your first user.
            </p>
            <Button onClick={handleAddUser}>
              <Plus className="h-4 w-4 mr-2" />
              Add User
            </Button>
          </div>
        )}

        {/* Edit User Drawer */}
        {isEditDrawerOpen && (
          <div className="fixed inset-0 z-50 overflow-hidden">
            {/* Backdrop */}
            <div 
              className="absolute inset-0 bg-black/50 transition-opacity"
              onClick={() => setIsEditDrawerOpen(false)}
            />
            
            {/* Drawer */}
            <div className="absolute right-0 top-0 h-full w-[600px] bg-white shadow-xl transform transition-transform">
              <div className="flex flex-col h-full">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b">
                  <div>
                    <h2 className="text-lg font-semibold">Edit User</h2>
                    <p className="text-sm text-muted-foreground">
                      Modify user details and role assignment
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setIsEditDrawerOpen(false)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                  {/* User Details */}
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="user-name">Full Name</Label>
                      <Input
                        id="user-name"
                        value={editForm.name}
                        onChange={(e) => setEditForm(prev => ({ ...prev, name: e.target.value }))}
                        placeholder="Enter full name"
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="user-email">Email Address</Label>
                      <Input
                        id="user-email"
                        type="email"
                        value={editForm.email}
                        onChange={(e) => setEditForm(prev => ({ ...prev, email: e.target.value }))}
                        placeholder="Enter email address"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="user-role">Role</Label>
                      <select
                        id="user-role"
                        value={editForm.role_id}
                        onChange={(e) => setEditForm(prev => ({ ...prev, role_id: e.target.value }))}
                        className="w-full px-3 py-2 border border-border rounded-md bg-background"
                      >
                        <option value="">Select a role</option>
                        {allRoles.map((role) => (
                          <option key={getId(role)} value={getId(role)}>
                            {role.name}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        id="user-active"
                        checked={editForm.is_active}
                        onChange={(e) => setEditForm(prev => ({ ...prev, is_active: e.target.checked }))}
                        className="rounded border-border"
                      />
                      <Label htmlFor="user-active">User is active</Label>
                    </div>
                  </div>
                </div>

                {/* Footer */}
                <div className="border-t p-6">
                  <div className="flex items-center justify-between">
                    <div className="text-sm text-muted-foreground">
                      {editForm.is_active ? 'Active user' : 'Inactive user'}
                    </div>
                    <div className="flex space-x-2">
                      <Button
                        variant="outline"
                        onClick={() => setIsEditDrawerOpen(false)}
                        disabled={saving}
                      >
                        Cancel
                      </Button>
                      <Button
                        onClick={handleSaveUser}
                        disabled={saving || !editForm.name.trim() || !editForm.email.trim() || !editForm.role_id}
                      >
                        {saving ? (
                          <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                            Saving...
                          </>
                        ) : (
                          <>
                            <Save className="h-4 w-4 mr-2" />
                            Save Changes
                          </>
                        )}
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Add User Drawer */}
        {isAddDrawerOpen && (
          <div className="fixed inset-0 z-50 overflow-hidden">
            {/* Backdrop */}
            <div 
              className="absolute inset-0 bg-black/50 transition-opacity"
              onClick={() => setIsAddDrawerOpen(false)}
            />
            
            {/* Drawer */}
            <div className="absolute right-0 top-0 h-full w-[600px] bg-white shadow-xl transform transition-transform">
              <div className="flex flex-col h-full">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b">
                  <div>
                    <h2 className="text-lg font-semibold">Add New User</h2>
                    <p className="text-sm text-muted-foreground">
                      Create a new user account with role assignment
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setIsAddDrawerOpen(false)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                  {/* User Details */}
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="add-user-name">Full Name</Label>
                      <Input
                        id="add-user-name"
                        value={addForm.name}
                        onChange={(e) => setAddForm(prev => ({ ...prev, name: e.target.value }))}
                        placeholder="Enter full name"
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="add-user-email">Email Address</Label>
                      <Input
                        id="add-user-email"
                        type="email"
                        value={addForm.email}
                        onChange={(e) => setAddForm(prev => ({ ...prev, email: e.target.value }))}
                        placeholder="Enter email address"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="add-user-password">Password</Label>
                      <Input
                        id="add-user-password"
                        type="password"
                        value={addForm.password}
                        onChange={(e) => setAddForm(prev => ({ ...prev, password: e.target.value }))}
                        placeholder="Enter password"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="add-user-role">Role</Label>
                      <select
                        id="add-user-role"
                        value={addForm.role_id}
                        onChange={(e) => setAddForm(prev => ({ ...prev, role_id: e.target.value }))}
                        className="w-full px-3 py-2 border border-border rounded-md bg-background"
                      >
                        <option value="">Select a role</option>
                        {allRoles.map((role) => (
                          <option key={getId(role)} value={getId(role)}>
                            {role.name}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        id="add-user-active"
                        checked={addForm.is_active}
                        onChange={(e) => setAddForm(prev => ({ ...prev, is_active: e.target.checked }))}
                        className="rounded border-border"
                      />
                      <Label htmlFor="add-user-active">User is active</Label>
                    </div>
                  </div>
                </div>

                {/* Footer */}
                <div className="border-t p-6">
                  <div className="flex items-center justify-between">
                    <div className="text-sm text-muted-foreground">
                      {addForm.is_active ? 'Active user' : 'Inactive user'}
                    </div>
                    <div className="flex space-x-2">
                      <Button
                        variant="outline"
                        onClick={() => setIsAddDrawerOpen(false)}
                        disabled={adding}
                      >
                        Cancel
                      </Button>
                      <Button
                        onClick={handleSaveNewUser}
                        disabled={adding || !addForm.name.trim() || !addForm.email.trim() || !addForm.password.trim() || !addForm.role_id}
                      >
                        {adding ? (
                          <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                            Creating...
                          </>
                        ) : (
                          <>
                            <Save className="h-4 w-4 mr-2" />
                            Create User
                          </>
                        )}
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Teacher Approval Drawer */}
        {approvalDrawerOpen && selectedTeacher && (
          <div className="fixed inset-0 z-50 overflow-hidden">
            {/* Backdrop */}
            <div 
              className="absolute inset-0 bg-black/50 transition-opacity"
              onClick={() => setApprovalDrawerOpen(false)}
            />
            
            {/* Drawer */}
            <div className="absolute right-0 top-0 h-full w-[600px] bg-white shadow-xl transform transition-transform">
              <div className="flex flex-col h-full">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b">
                  <div>
                    <h2 className="text-lg font-semibold">Teacher Approval</h2>
                    <p className="text-sm text-muted-foreground">
                      Review and approve teacher account request
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setApprovalDrawerOpen(false)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                  {/* Teacher Details */}
                  <div className="space-y-4">
                    <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                      <div className="flex items-center space-x-2">
                        <Users className="h-4 w-4 text-gray-500" />
                        <span className="font-medium text-gray-900">Teacher Information</span>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="text-gray-500">Name:</span>
                          <div className="font-medium">{selectedTeacher.name}</div>
                        </div>
                        <div>
                          <span className="text-gray-500">Email:</span>
                          <div className="font-medium">{selectedTeacher.email}</div>
                        </div>
                        <div>
                          <span className="text-gray-500">Requested Role:</span>
                          <div className="font-medium">{selectedTeacher.requested_role_name}</div>
                        </div>
                        <div>
                          <span className="text-gray-500">Request Date:</span>
                          <div className="font-medium">{new Date(selectedTeacher.created_at).toLocaleDateString()}</div>
                        </div>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="approval-reason">Approval Reason (Optional)</Label>
                      <Textarea
                        id="approval-reason"
                        value={approvalReason}
                        onChange={(e) => setApprovalReason(e.target.value)}
                        placeholder="Enter reason for approval or rejection..."
                        rows={4}
                        className="resize-none"
                      />
                      <p className="text-xs text-gray-500">
                        This reason will be recorded in the system for audit purposes.
                      </p>
                    </div>
                  </div>
                </div>

                {/* Footer */}
                <div className="border-t p-6">
                  <div className="flex items-center justify-between">
                    <div className="text-sm text-muted-foreground">
                      This action will be recorded in the audit log
                    </div>
                    <div className="flex space-x-2">
                      <Button
                        variant="outline"
                        onClick={() => setApprovalDrawerOpen(false)}
                        disabled={approving}
                      >
                        Cancel
                      </Button>
                      <Button
                        variant="outline"
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                        onClick={() => submitTeacherApproval('reject')}
                        disabled={approving}
                      >
                        {approving ? (
                          <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-red-600 mr-2"></div>
                            Rejecting...
                          </>
                        ) : (
                          <>
                            <XCircle className="h-4 w-4 mr-2" />
                            Reject
                          </>
                        )}
                      </Button>
                      <Button
                        className="bg-green-600 hover:bg-green-700 text-white"
                        onClick={() => submitTeacherApproval('approve')}
                        disabled={approving}
                      >
                        {approving ? (
                          <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                            Approving...
                          </>
                        ) : (
                          <>
                            <CheckCircle className="h-4 w-4 mr-2" />
                            Approve
                          </>
                        )}
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </>
      </DashboardLayout>
    </RouteGuard>
  )
}
