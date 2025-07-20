"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { DashboardLayout } from "@/components/layout/dashboard-layout"
import { Plus, Users, Shield, Edit, Trash2, X, Save, Calendar, ArrowUpDown } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { toast } from "sonner"

// Types
interface Permission {
  id?: string
  _id?: string
  name: string
  description: string
  resource: string
  action: string
  created_at: string
}

interface Role {
  id?: string
  _id?: string
  name: string
  description: string
  permission_ids: string[]
  permissions: Permission[]
  user_count: number
  created_at: string
  updated_at: string
}

export default function Roles() {
  const [roles, setRoles] = useState<Role[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [allPermissions, setAllPermissions] = useState<Permission[]>([])
  
  // Edit drawer state
  const [isEditDrawerOpen, setIsEditDrawerOpen] = useState(false)
  const [editingRole, setEditingRole] = useState<Role | null>(null)
  const [editForm, setEditForm] = useState({
    name: '',
    description: '',
    permission_ids: [] as string[]
  })
  const [saving, setSaving] = useState(false)

  // Sorting state
  const [sortField, setSortField] = useState<keyof Role | 'permission_count'>('name')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc')

  // Permissions view drawer state
  const [isPermissionsDrawerOpen, setIsPermissionsDrawerOpen] = useState(false)
  const [viewingRolePermissions, setViewingRolePermissions] = useState<Role | null>(null)

  // Helper function to get ID from either id or _id field
  const getId = (item: Role | Permission): string => {
    return item.id || item._id || Math.random().toString(36).substr(2, 9)
  }

  // Fetch all permissions for the edit form
  const fetchAllPermissions = async () => {
    try {
      const token = localStorage.getItem('auth_token')
      
      const response = await fetch('http://localhost:8000/masters/permissions/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })

      if (response.ok) {
        const data = await response.json()
        setAllPermissions(data)
      }
    } catch (err) {
      console.error('Error fetching permissions:', err)
    }
  }

  // Handle edit role
  const handleEditRole = (role: Role) => {
    setEditingRole(role)
    setEditForm({
      name: role.name,
      description: role.description,
      permission_ids: role.permission_ids
    })
    setIsEditDrawerOpen(true)
  }

  // Handle save role
  const handleSaveRole = async () => {
    if (!editingRole) return

    try {
      setSaving(true)
      const token = localStorage.getItem('auth_token')
      const roleId = getId(editingRole)
      
      const response = await fetch(`http://localhost:8000/masters/roles/${roleId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(editForm)
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to update role')
      }

      // Get the updated role data from the response
      const updatedRole = await response.json()
      
      // Update the local state with the new role data
      setRoles(prevRoles => 
        prevRoles.map(role => 
          getId(role) === getId(editingRole) ? updatedRole : role
        )
      )
      
      setIsEditDrawerOpen(false)
      setEditingRole(null)
      toast.success(`Role "${editForm.name}" has been updated successfully.`)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred'
      toast.error("Failed to update role", {
        description: errorMessage,
      })
      console.error('Error updating role:', err)
    } finally {
      setSaving(false)
    }
  }

  // Get action icon (same as permissions page)
  const getActionIcon = (action: string) => {
    switch (action) {
      case 'read': return '👁️'
      case 'create': return '➕'
      case 'update': return '✏️'
      case 'delete': return '🗑️'
      case 'admin': return '👑'
      case 'manage': return '⚙️'
      default: return '🔧'
    }
  }

  // Get action badge color
  const getActionBadgeColor = (action: string) => {
    switch (action) {
      case 'read': return 'bg-green-100 text-green-800'
      case 'create': return 'bg-blue-100 text-blue-800'
      case 'update': return 'bg-yellow-100 text-yellow-800'
      case 'delete': return 'bg-red-100 text-red-800'
      case 'admin': return 'bg-purple-100 text-purple-800'
      case 'manage': return 'bg-orange-100 text-orange-800'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  // Handle permission toggle
  const handlePermissionToggle = (permissionId: string) => {
    setEditForm(prev => ({
      ...prev,
      permission_ids: prev.permission_ids.includes(permissionId)
        ? prev.permission_ids.filter(id => id !== permissionId)
        : [...prev.permission_ids, permissionId]
    }))
  }

  // Handle view permissions
  const handleViewPermissions = (role: Role) => {
    setViewingRolePermissions(role)
    setIsPermissionsDrawerOpen(true)
  }

  // Handle delete role
  const handleDeleteRole = async (role: Role) => {
    const roleId = getId(role)
    const confirmDelete = window.confirm(
      `Are you sure you want to delete the role "${role.name}"?\n\n` +
      `This role currently has ${role.user_count} user(s) assigned to it.\n\n` +
      `This action cannot be undone.`
    )
    
    if (!confirmDelete) return

    try {
      const token = localStorage.getItem('auth_token')
      
      const response = await fetch(`http://localhost:8000/masters/roles/${roleId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to delete role')
      }

      // Refresh the roles list
      await fetchRoles()
      toast.success(`Role "${role.name}" has been deleted successfully.`)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred'
      toast.error("Failed to delete role", {
        description: errorMessage,
      })
      console.error('Error deleting role:', err)
    }
  }

  // Fetch roles from API
  const fetchRoles = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('auth_token')
      
      const response = await fetch('http://localhost:8000/masters/roles/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error('Failed to fetch roles')
      }

      const data = await response.json()
      setRoles(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
      console.error('Error fetching roles:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchRoles()
    fetchAllPermissions()
  }, [])

  // Handle sorting
  const handleSort = (field: keyof Role | 'permission_count') => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
  }

  // Sort roles
  const sortedRoles = [...roles].sort((a, b) => {
    let aValue: string | number | Date
    let bValue: string | number | Date

    switch (sortField) {
      case 'permission_count':
        aValue = a.permissions.length
        bValue = b.permissions.length
        break
      case 'created_at':
        aValue = new Date(a.created_at)
        bValue = new Date(b.created_at)
        break
      case 'user_count':
        aValue = a.user_count
        bValue = b.user_count
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
  const totalUsers = roles.reduce((sum, role) => sum + (role.user_count || 0), 0)
  const mostUsedRole = roles.length > 0 
    ? roles.reduce((prev, current) => 
        ((prev.user_count || 0) > (current.user_count || 0)) ? prev : current
      )
    : null


  if (loading) {
    return (
      <DashboardLayout 
        title="Roles Management" 
        showBackButton={true}
        backUrl="/masters"
        backLabel="Back to Masters"
      >
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
            <p className="mt-2 text-sm text-muted-foreground">Loading roles...</p>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  if (error) {
    return (
      <DashboardLayout 
        title="Roles Management" 
        showBackButton={true}
        backUrl="/masters"
        backLabel="Back to Masters"
      >
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <p className="text-red-600">Error: {error}</p>
            <Button onClick={fetchRoles} className="mt-4">
              Try Again
            </Button>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout 
      title="Roles Management" 
      showBackButton={true}
      backUrl="/masters"
      backLabel="Back to Masters"
      actions={
        <Button className="flex items-center">
          <Plus className="h-4 w-4 mr-2" />
          Add New Role
        </Button>
      }
    >
      <>
        {/* Stats Cards */}
        <div key="stats-section" className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {[
            {
              key: "total-roles",
              title: "Total Roles",
              value: roles.length,
              description: "Active roles in system",
              icon: Shield
            },
            {
              key: "total-users", 
              title: "Total Assignments",
              value: totalUsers,
              description: "Total role assignments",
              icon: Users
            },
            {
              key: "most-used-role",
              title: "Most Used Role", 
              value: mostUsedRole?.name || 'N/A',
              description: `${mostUsedRole?.user_count || 0} users assigned`,
              icon: Users
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

        {/* Roles Table */}
        <Card key="roles-section">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg font-semibold">All Roles</CardTitle>
              <div className="text-sm text-muted-foreground">
                {roles.length} role{roles.length !== 1 ? 's' : ''} total
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
                      Role Name
                    </TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead 
                      sortable 
                      sortDirection={sortField === 'user_count' ? sortDirection : null}
                      onSort={() => handleSort('user_count')}
                    >
                      <div className="flex items-center space-x-2">
                        <Users className="h-4 w-4 text-muted-foreground" />
                        <span>Users</span>
                      </div>
                    </TableHead>
                    <TableHead 
                      sortable 
                      sortDirection={sortField === 'permission_count' ? sortDirection : null}
                      onSort={() => handleSort('permission_count')}
                    >
                      <div className="flex items-center space-x-2">
                        <Shield className="h-4 w-4 text-muted-foreground" />
                        <span>Permissions</span>
                      </div>
                    </TableHead>
                    <TableHead 
                      sortable 
                      sortDirection={sortField === 'created_at' ? sortDirection : null}
                      onSort={() => handleSort('created_at')}
                    >
                      <div className="flex items-center space-x-2">
                        <Calendar className="h-4 w-4 text-muted-foreground" />
                        <span>Created</span>
                      </div>
                    </TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sortedRoles.map((role) => {
                    const roleId = getId(role)
                    return (
                      <TableRow key={roleId}>
                        <TableCell>
                          <div className="font-medium">{role.name}</div>
                        </TableCell>
                        <TableCell>
                          <span className="text-sm text-muted-foreground">{role.description}</span>
                        </TableCell>
                        <TableCell>
                          <Badge 
                            variant="outline"
                            className="text-xs bg-blue-100 text-blue-800 border-blue-200"
                          >
                            {role.user_count} user{role.user_count !== 1 ? 's' : ''}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center space-x-2">
                            <Badge 
                              variant="outline"
                              className="text-xs bg-green-100 text-green-800 border-green-200"
                            >
                              {role.permissions.length} permission{role.permissions.length !== 1 ? 's' : ''}
                            </Badge>
                            {role.permissions.length > 0 && (
                              <button
                                onClick={() => handleViewPermissions(role)}
                                className="text-sm text-blue-600 hover:text-blue-800 underline cursor-pointer"
                              >
                                View Details
                              </button>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <span className="text-sm">
                            {new Date(role.created_at).toLocaleDateString()}
                          </span>
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex items-center space-x-2">
                            <Button 
                              variant="outline" 
                              size="sm"
                              onClick={() => handleEditRole(role)}
                            >
                              <Edit className="h-4 w-4 mr-1" />
                              Edit
                            </Button>
                            <Button 
                              variant="outline" 
                              size="sm" 
                              className="text-destructive hover:text-destructive"
                              onClick={() => handleDeleteRole(role)}
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
        {roles.length === 0 && (
          <div key="empty-state" className="text-center py-12">
            <Shield className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">No roles found</h3>
            <p className="text-muted-foreground mb-4">
              Get started by creating your first role.
            </p>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Add Role
            </Button>
          </div>
        )}

        {/* Edit Role Drawer */}
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
                    <h2 className="text-lg font-semibold">Edit Role</h2>
                    <p className="text-sm text-muted-foreground">
                      Modify role details and permissions
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
                  {/* Role Details */}
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="role-name">Role Name</Label>
                      <Input
                        id="role-name"
                        value={editForm.name}
                        onChange={(e) => setEditForm(prev => ({ ...prev, name: e.target.value }))}
                        placeholder="Enter role name"
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="role-description">Description</Label>
                      <Input
                        id="role-description"
                        value={editForm.description}
                        onChange={(e) => setEditForm(prev => ({ ...prev, description: e.target.value }))}
                        placeholder="Enter role description"
                      />
                    </div>
                  </div>

                  {/* Permissions */}
                  <div className="space-y-4">
                    <div>
                      <Label>Permissions</Label>
                      <p className="text-sm text-muted-foreground">
                        Select the permissions for this role
                      </p>
                    </div>

                    {/* Debug info */}
                    {allPermissions.length === 0 && (
                      <div className="text-sm text-muted-foreground p-4 bg-gray-50 rounded">
                        <p>Loading permissions... ({allPermissions.length} permissions loaded)</p>
                        <p className="text-xs mt-1">If this persists, check the API connection.</p>
                      </div>
                    )}

                    {/* Group permissions by resource - Card Layout */}
                    {allPermissions.length > 0 && Object.entries(
                      allPermissions.reduce((acc, permission) => {
                        if (!acc[permission.resource]) {
                          acc[permission.resource] = []
                        }
                        acc[permission.resource].push(permission)
                        return acc
                      }, {} as Record<string, Permission[]>)
                    ).map(([resource, resourcePermissions]) => (
                      <div key={resource} className="space-y-3">
                        <div className="flex items-center justify-between">
                          <h4 className="font-semibold text-base capitalize text-gray-800">
                            {resource}
                          </h4>
                          <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                            {resourcePermissions.filter(p => editForm.permission_ids.includes(getId(p))).length} / {resourcePermissions.length}
                          </span>
                        </div>
                        
                        {/* Permission Cards Grid */}
                        <div className="grid gap-3">
                          {resourcePermissions.map((permission) => {
                            const permissionId = getId(permission)
                            const isChecked = editForm.permission_ids.includes(permissionId)
                            
                            return (
                              <div
                                key={permissionId}
                                onClick={() => handlePermissionToggle(permissionId)}
                                className={`
                                  flex items-center justify-between p-3 border rounded-lg cursor-pointer transition-all duration-200
                                  ${isChecked 
                                    ? 'border-primary/20 bg-accent/50' 
                                    : 'border-border hover:bg-gray-50'
                                  }
                                `}
                              >
                                <div className="flex items-center space-x-3">
                                  <Checkbox
                                    checked={isChecked}
                                    onChange={() => handlePermissionToggle(permissionId)}
                                  />
                                  <span className="text-lg">{getActionIcon(permission.action)}</span>
                                  <div>
                                    <div className="font-medium">{permission.name}</div>
                                    <div className="text-sm text-muted-foreground">{permission.description}</div>
                                  </div>
                                </div>
                                <div className="flex items-center space-x-2">
                                  <span className={`px-2 py-1 rounded text-xs font-medium ${getActionBadgeColor(permission.action)}`}>
                                    {permission.action}
                                  </span>
                                </div>
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    ))}

                    {/* Show total permissions loaded */}
                    {allPermissions.length > 0 && (
                      <div className="text-xs text-muted-foreground p-2 bg-blue-50 rounded">
                        Total permissions loaded: {allPermissions.length}
                      </div>
                    )}
                  </div>
                </div>

                {/* Footer */}
                <div className="border-t p-6">
                  <div className="flex items-center justify-between">
                    <div className="text-sm text-muted-foreground">
                      {editForm.permission_ids.length} permission{editForm.permission_ids.length !== 1 ? 's' : ''} selected
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
                        onClick={handleSaveRole}
                        disabled={saving || !editForm.name.trim()}
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

        {/* View Permissions Drawer */}
        {isPermissionsDrawerOpen && viewingRolePermissions && (
          <div className="fixed inset-0 z-50 overflow-hidden">
            {/* Backdrop */}
            <div 
              className="absolute inset-0 bg-black/50 transition-opacity"
              onClick={() => setIsPermissionsDrawerOpen(false)}
            />
            
            {/* Drawer */}
            <div className="absolute right-0 top-0 h-full w-[600px] bg-white shadow-xl transform transition-transform">
              <div className="flex flex-col h-full">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b">
                  <div>
                    <h2 className="text-lg font-semibold">Role Permissions</h2>
                    <p className="text-sm text-muted-foreground">
                      Permissions assigned to "{viewingRolePermissions.name}"
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setIsPermissionsDrawerOpen(false)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                  {/* Role Info */}
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <div className="flex items-center space-x-3 mb-2">
                      <div className="p-2 bg-primary/10 rounded-lg">
                        <Shield className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <h3 className="font-semibold">{viewingRolePermissions.name}</h3>
                        <p className="text-sm text-muted-foreground">{viewingRolePermissions.description}</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                      <span>{viewingRolePermissions.user_count} users assigned</span>
                      <span>{viewingRolePermissions.permissions.length} permissions</span>
                    </div>
                  </div>

                  {/* Permissions List */}
                  {viewingRolePermissions.permissions.length === 0 ? (
                    <div className="text-center py-8">
                      <Shield className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                      <h3 className="text-lg font-medium mb-2">No permissions assigned</h3>
                      <p className="text-muted-foreground">
                        This role doesn't have any permissions assigned yet.
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-6">
                      {Object.entries(
                        viewingRolePermissions.permissions.reduce((acc, permission) => {
                          if (!acc[permission.resource]) {
                            acc[permission.resource] = []
                          }
                          acc[permission.resource].push(permission)
                          return acc
                        }, {} as Record<string, Permission[]>)
                      ).map(([resource, resourcePermissions]) => (
                        <div key={resource} className="space-y-3">
                          <div className="flex items-center justify-between">
                            <h4 className="font-semibold text-base capitalize text-gray-800">
                              {resource}
                            </h4>
                            <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                              {resourcePermissions.length} permission{resourcePermissions.length !== 1 ? 's' : ''}
                            </span>
                          </div>
                          
                          {/* Permission Cards Grid */}
                          <div className="grid gap-3">
                            {resourcePermissions.map((permission) => {
                              const permissionId = getId(permission)
                              
                              return (
                                <div
                                  key={permissionId}
                                  className="flex items-center justify-between p-3 border rounded-lg border-border bg-white"
                                >
                                  <div className="flex items-center space-x-3">
                                    <span className="text-lg">{getActionIcon(permission.action)}</span>
                                    <div>
                                      <div className="font-medium">{permission.name}</div>
                                      <div className="text-sm text-muted-foreground">{permission.description}</div>
                                    </div>
                                  </div>
                                  <div className="flex items-center space-x-2">
                                    <span className={`px-2 py-1 rounded text-xs font-medium ${getActionBadgeColor(permission.action)}`}>
                                      {permission.action}
                                    </span>
                                  </div>
                                </div>
                              )
                            })}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Footer */}
                <div className="border-t p-6">
                  <div className="flex items-center justify-between">
                    <div className="text-sm text-muted-foreground">
                      Total: {viewingRolePermissions.permissions.length} permission{viewingRolePermissions.permissions.length !== 1 ? 's' : ''}
                    </div>
                    <Button
                      variant="outline"
                      onClick={() => setIsPermissionsDrawerOpen(false)}
                    >
                      Close
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </>
    </DashboardLayout>
  )
}
