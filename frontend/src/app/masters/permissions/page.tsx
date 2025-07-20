"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { DashboardLayout } from "@/components/layout/dashboard-layout"
import { Plus, Shield, Edit, Trash2, Tag, Activity, X, Save, ArrowUpDown, Eye, UserPlus, Settings, Crown } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Combobox } from "@/components/ui/combobox"
import { Badge } from "@/components/ui/badge"
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

export default function Permissions() {
  const [permissions, setPermissions] = useState<Permission[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // Edit/Create drawer state
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)
  const [editingPermission, setEditingPermission] = useState<Permission | null>(null)
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    resource: '',
    action: ''
  })
  const [saving, setSaving] = useState(false)
  
  // Combobox options state
  const [resourceOptions, setResourceOptions] = useState<Array<{value: string, label: string}>>([])
  const [actionOptions, setActionOptions] = useState<Array<{value: string, label: string}>>([])
  const [loadingOptions, setLoadingOptions] = useState(false)

  // Sorting state
  const [sortField, setSortField] = useState<keyof Permission>('resource')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc')
  
  // View options
  const [groupByCategory, setGroupByCategory] = useState(false)

  // Helper function to get ID from either id or _id field
  const getId = (permission: Permission): string => {
    return permission.id || permission._id || ''
  }

  // Fetch permissions from API
  const fetchPermissions = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('auth_token')
      
      const response = await fetch('http://localhost:8000/masters/permissions/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error('Failed to fetch permissions')
      }

      const data = await response.json()
      setPermissions(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
      console.error('Error fetching permissions:', err)
    } finally {
      setLoading(false)
    }
  }

  // Fetch resource and action options
  const fetchOptions = async () => {
    try {
      setLoadingOptions(true)
      const token = localStorage.getItem('auth_token')
      
      // Fetch categories (previously resources)
      const categoriesResponse = await fetch('http://localhost:8000/masters/permissions/resources', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })
      
      // Fetch actions
      const actionsResponse = await fetch('http://localhost:8000/masters/permissions/actions', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })

      if (categoriesResponse.ok) {
        const categoriesData = await categoriesResponse.json()
        setResourceOptions(
          categoriesData.resources.map((resource: string) => ({
            value: resource,
            label: resource.charAt(0).toUpperCase() + resource.slice(1)
          }))
        )
      }

      if (actionsResponse.ok) {
        const actionsData = await actionsResponse.json()
        setActionOptions(
          actionsData.actions.map((action: string) => ({
            value: action,
            label: action.charAt(0).toUpperCase() + action.slice(1)
          }))
        )
      }
    } catch (err) {
      console.error('Error fetching options:', err)
    } finally {
      setLoadingOptions(false)
    }
  }

  useEffect(() => {
    fetchPermissions()
  }, [])

  // Handle create permission
  const handleCreatePermission = async () => {
    setEditingPermission(null)
    setFormData({
      name: '',
      description: '',
      resource: '',
      action: ''
    })
    setIsDrawerOpen(true)
    await fetchOptions()
  }

  // Handle edit permission
  const handleEditPermission = async (permission: Permission) => {
    setEditingPermission(permission)
    setFormData({
      name: permission.name,
      description: permission.description,
      resource: permission.resource,
      action: permission.action
    })
    setIsDrawerOpen(true)
    await fetchOptions()
  }

  // Handle save permission
  const handleSavePermission = async () => {
    try {
      setSaving(true)
      const token = localStorage.getItem('auth_token')
      
      const url = editingPermission 
        ? `http://localhost:8000/masters/permissions/${getId(editingPermission)}`
        : 'http://localhost:8000/masters/permissions/'
      
      const method = editingPermission ? 'PUT' : 'POST'
      
      const response = await fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to save permission')
      }

      await fetchPermissions()
      setIsDrawerOpen(false)
      setEditingPermission(null)
      
      toast.success(
        editingPermission 
          ? `Permission "${formData.name}" has been updated successfully.`
          : `Permission "${formData.name}" has been created successfully.`
      )
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred'
      toast.error("Failed to save permission", {
        description: errorMessage,
      })
      console.error('Error saving permission:', err)
    } finally {
      setSaving(false)
    }
  }

  // Handle delete permission
  const handleDeletePermission = async (permission: Permission) => {
    const confirmDelete = window.confirm(
      `Are you sure you want to delete the permission "${permission.name}"?\n\n` +
      `Category: ${permission.resource}\n` +
      `Action: ${permission.action}\n\n` +
      `This action cannot be undone.`
    )
    
    if (!confirmDelete) return

    try {
      const token = localStorage.getItem('auth_token')
      
      const response = await fetch(`http://localhost:8000/masters/permissions/${getId(permission)}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to delete permission')
      }

      await fetchPermissions()
      toast.success(`Permission "${permission.name}" has been deleted successfully.`)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred'
      toast.error("Failed to delete permission", {
        description: errorMessage,
      })
      console.error('Error deleting permission:', err)
    }
  }

  // Handle sorting
  const handleSort = (field: keyof Permission) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
  }

  // Sort permissions
  const sortedPermissions = [...permissions].sort((a, b) => {
    let aValue: string | Date
    let bValue: string | Date

    switch (sortField) {
      case 'created_at':
        aValue = new Date(a.created_at)
        bValue = new Date(b.created_at)
        break
      default:
        aValue = String(a[sortField]).toLowerCase()
        bValue = String(b[sortField]).toLowerCase()
    }

    if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1
    if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1
    return 0
  })

  // Get category color with enhanced styling
  const getCategoryColor = (category: string) => {
    const colors = {
      users: 'bg-blue-50 text-blue-900 border-blue-300 shadow-sm ring-1 ring-blue-200',
      roles: 'bg-emerald-50 text-emerald-900 border-emerald-300 shadow-sm ring-1 ring-emerald-200',
      permissions: 'bg-purple-50 text-purple-900 border-purple-300 shadow-sm ring-1 ring-purple-200',
      dashboard: 'bg-orange-50 text-orange-900 border-orange-300 shadow-sm ring-1 ring-orange-200',
      masters: 'bg-rose-50 text-rose-900 border-rose-300 shadow-sm ring-1 ring-rose-200',
      content: 'bg-amber-50 text-amber-900 border-amber-300 shadow-sm ring-1 ring-amber-200',
      profile: 'bg-slate-50 text-slate-900 border-slate-300 shadow-sm ring-1 ring-slate-200',
    }
    return colors[category as keyof typeof colors] || 'bg-slate-50 text-slate-900 border-slate-300 shadow-sm ring-1 ring-slate-200'
  }

  // Get action color with enhanced styling
  const getActionColor = (action: string) => {
    const colors = {
      read: 'bg-sky-50 text-sky-900 border-sky-300 shadow-sm ring-1 ring-sky-200',
      create: 'bg-green-50 text-green-900 border-green-300 shadow-sm ring-1 ring-green-200',
      update: 'bg-yellow-50 text-yellow-900 border-yellow-300 shadow-sm ring-1 ring-yellow-200',
      delete: 'bg-red-50 text-red-900 border-red-300 shadow-sm ring-1 ring-red-200',
      admin: 'bg-violet-50 text-violet-900 border-violet-300 shadow-sm ring-1 ring-violet-200',
      manage: 'bg-orange-50 text-orange-900 border-orange-300 shadow-sm ring-1 ring-orange-200',
    }
    return colors[action as keyof typeof colors] || 'bg-gray-50 text-gray-900 border-gray-300 shadow-sm ring-1 ring-gray-200'
  }

  // Get row background based on category for subtle grouping
  const getRowBackground = (category: string, index: number) => {
    const categoryBackgrounds = {
      users: 'hover:bg-blue-50/50',
      roles: 'hover:bg-emerald-50/50',
      permissions: 'hover:bg-purple-50/50',
      dashboard: 'hover:bg-orange-50/50',
      masters: 'hover:bg-rose-50/50',
      content: 'hover:bg-amber-50/50',
      profile: 'hover:bg-slate-50/50',
    }
    const baseHover = categoryBackgrounds[category as keyof typeof categoryBackgrounds] || 'hover:bg-gray-50/50'
    const alternating = index % 2 === 0 ? 'bg-white' : 'bg-gray-50/30'
    return `${alternating} ${baseHover} transition-colors duration-150`
  }

  // Get action icon
  const getActionIcon = (action: string) => {
    switch (action) {
      case 'read': return Eye
      case 'create': return Plus
      case 'update': return Edit
      case 'delete': return Trash2
      case 'admin': return Crown
      case 'manage': return Settings
      default: return Activity
    }
  }

  // Group permissions by category for stats
  const groupedPermissions = permissions.reduce((acc, permission) => {
    if (!acc[permission.resource]) {
      acc[permission.resource] = []
    }
    acc[permission.resource].push(permission)
    return acc
  }, {} as Record<string, Permission[]>)

  if (loading) {
    return (
      <DashboardLayout 
        title="Permissions Management" 
        showBackButton={true}
        backUrl="/masters"
        backLabel="Back to Masters"
      >
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
            <p className="mt-2 text-sm text-muted-foreground">Loading permissions...</p>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  if (error) {
    return (
      <DashboardLayout 
        title="Permissions Management" 
        showBackButton={true}
        backUrl="/masters"
        backLabel="Back to Masters"
      >
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <p className="text-red-600">Error: {error}</p>
            <Button onClick={fetchPermissions} className="mt-4">
              Try Again
            </Button>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout 
      title="Permissions Management" 
      showBackButton={true}
      backUrl="/masters"
      backLabel="Back to Masters"
      actions={
        <Button className="flex items-center" onClick={handleCreatePermission}>
          <Plus className="h-4 w-4 mr-2" />
          Add New Permission
        </Button>
      }
    >
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card key="total-permissions">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Permissions</CardTitle>
              <Shield className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{permissions.length}</div>
              <p className="text-xs text-muted-foreground">System permissions</p>
            </CardContent>
          </Card>

          <Card key="total-categories">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Categories</CardTitle>
              <Tag className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{Object.keys(groupedPermissions).length}</div>
              <p className="text-xs text-muted-foreground">Different categories</p>
            </CardContent>
          </Card>

          <Card key="total-actions">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Actions</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {[...new Set(permissions.map(p => p.action))].length}
              </div>
              <p className="text-xs text-muted-foreground">Unique actions</p>
            </CardContent>
          </Card>
        </div>

        {/* Permissions Table */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg font-semibold">All Permissions</CardTitle>
              <div className="text-sm text-muted-foreground">
                {permissions.length} permission{permissions.length !== 1 ? 's' : ''} total
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
                    <TableHead>Description</TableHead>
                    <TableHead 
                      sortable 
                      sortDirection={sortField === 'resource' ? sortDirection : null}
                      onSort={() => handleSort('resource')}
                    >
                      <div className="flex items-center space-x-2">
                        <Tag className="h-4 w-4 text-muted-foreground" />
                        <span>Category</span>
                      </div>
                    </TableHead>
                    <TableHead 
                      sortable 
                      sortDirection={sortField === 'action' ? sortDirection : null}
                      onSort={() => handleSort('action')}
                    >
                      <div className="flex items-center space-x-2">
                        <Activity className="h-4 w-4 text-muted-foreground" />
                        <span>Action</span>
                      </div>
                    </TableHead>
                    <TableHead 
                      sortable 
                      sortDirection={sortField === 'created_at' ? sortDirection : null}
                      onSort={() => handleSort('created_at')}
                    >
                      Created
                    </TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sortedPermissions.map((permission, index) => {
                    const permissionId = getId(permission)
                    return (
                      <TableRow 
                        key={permissionId}
                        className={getRowBackground(permission.resource, index)}
                      >
                        <TableCell>
                          <div className="font-medium">{permission.name}</div>
                        </TableCell>
                        <TableCell>
                          <span className="text-sm text-muted-foreground">{permission.description}</span>
                        </TableCell>
                        <TableCell>
                          <Badge 
                            variant="outline" 
                            className={`text-xs font-medium ${getCategoryColor(permission.resource)}`}
                          >
                            <div className="flex items-center space-x-1">
                              <Tag className="h-3 w-3" />
                              <span>{permission.resource}</span>
                            </div>
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge 
                            variant="outline"
                            className={`text-xs font-medium ${getActionColor(permission.action)}`}
                          >
                            <div className="flex items-center space-x-1">
                              {(() => {
                                const IconComponent = getActionIcon(permission.action)
                                return <IconComponent className="h-3 w-3" />
                              })()}
                              <span>{permission.action}</span>
                            </div>
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <span className="text-sm">
                            {new Date(permission.created_at).toLocaleDateString()}
                          </span>
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex items-center justify-end space-x-2">
                            <Button 
                              variant="outline" 
                              size="sm"
                              onClick={() => handleEditPermission(permission)}
                              className="hover:bg-blue-50 hover:border-blue-300"
                            >
                              <Edit className="h-4 w-4 mr-1" />
                              Edit
                            </Button>
                            <Button 
                              variant="outline" 
                              size="sm" 
                              className="text-destructive hover:text-destructive hover:bg-red-50 hover:border-red-300"
                              onClick={() => handleDeletePermission(permission)}
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
        {permissions.length === 0 && (
          <div className="text-center py-12">
            <Shield className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">No permissions found</h3>
            <p className="text-muted-foreground mb-4">
              Get started by creating your first permission.
            </p>
            <Button onClick={handleCreatePermission}>
              <Plus className="h-4 w-4 mr-2" />
              Add Permission
            </Button>
          </div>
        )}

        {/* Create/Edit Permission Drawer */}
        {isDrawerOpen && (
          <div className="fixed inset-0 z-50 overflow-hidden">
            {/* Backdrop */}
            <div 
              className="absolute inset-0 bg-black/50 transition-opacity"
              onClick={() => setIsDrawerOpen(false)}
            />
            
            {/* Drawer */}
            <div className="absolute right-0 top-0 h-full w-[500px] bg-white shadow-xl transform transition-transform">
              <div className="flex flex-col h-full">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b">
                  <div>
                    <h2 className="text-lg font-semibold">
                      {editingPermission ? 'Edit Permission' : 'Create Permission'}
                    </h2>
                    <p className="text-sm text-muted-foreground">
                      {editingPermission ? 'Modify permission details' : 'Add a new system permission'}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setIsDrawerOpen(false)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="permission-name">Permission Name</Label>
                      <Input
                        id="permission-name"
                        value={formData.name}
                        onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                        placeholder="e.g., user_create, role_read"
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="permission-description">Description</Label>
                      <Input
                        id="permission-description"
                        value={formData.description}
                        onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                        placeholder="Describe what this permission allows"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="permission-category">Category</Label>
                      <Combobox
                        options={resourceOptions}
                        value={formData.resource}
                        onValueChange={(value) => setFormData(prev => ({ ...prev, resource: value }))}
                        placeholder="Select or create category..."
                        searchPlaceholder="Search or type to add new category"
                        emptyText="No categories found."
                        createText="Create category"
                        disabled={loadingOptions}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="permission-action">Action</Label>
                      <Combobox
                        options={actionOptions}
                        value={formData.action}
                        onValueChange={(value) => setFormData(prev => ({ ...prev, action: value }))}
                        placeholder="Select or create action..."
                        searchPlaceholder="Search or type to add new action"
                        emptyText="No actions found."
                        createText="Create action"
                        disabled={loadingOptions}
                      />
                    </div>
                  </div>
                </div>

                {/* Footer */}
                <div className="border-t p-6">
                  <div className="flex items-center justify-between">
                    <div className="text-sm text-muted-foreground">
                      {editingPermission ? 'Update existing permission' : 'Create new permission'}
                    </div>
                    <div className="flex space-x-2">
                      <Button
                        variant="outline"
                        onClick={() => setIsDrawerOpen(false)}
                        disabled={saving}
                      >
                        Cancel
                      </Button>
                      <Button
                        onClick={handleSavePermission}
                        disabled={saving || !formData.name.trim() || !formData.description.trim() || !formData.resource.trim() || !formData.action.trim()}
                      >
                        {saving ? (
                          <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                            Saving...
                          </>
                        ) : (
                          <>
                            <Save className="h-4 w-4 mr-2" />
                            {editingPermission ? 'Update Permission' : 'Create Permission'}
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
    </DashboardLayout>
  )
}
