"use client"

import { useState } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { GraduationCap, Users, BookOpen, Award } from "lucide-react"

interface RoleSelectorProps {
  selectedRole: string
  onRoleChange: (role: string) => void
  showDescription?: boolean
}

export function RoleSelector({ selectedRole, onRoleChange, showDescription = true }: RoleSelectorProps) {
  return (
    <div className="w-full mb-6">
      <Tabs value={selectedRole} onValueChange={onRoleChange} className="w-full">
        <TabsList className="grid w-full grid-cols-2 mb-4">
          <TabsTrigger value="Student" className="flex items-center gap-2">
            <GraduationCap className="w-4 h-4" />
            Student
          </TabsTrigger>
          <TabsTrigger value="Teacher" className="flex items-center gap-2">
            <Users className="w-4 h-4" />
            Teacher
          </TabsTrigger>
        </TabsList>
        
        {showDescription && (
          <>
            <TabsContent value="Student" className="mt-4">
              <Card className="border-blue-200 bg-blue-50/50">
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg flex items-center gap-2 text-blue-800">
                    <GraduationCap className="w-5 h-5" />
                    Student Account
                  </CardTitle>
                  <CardDescription className="text-blue-700">
                    Access courses, complete assignments, and track your learning progress
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm text-blue-700">
                      <BookOpen className="w-4 h-4" />
                      <span>Enroll in courses and access learning materials</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-blue-700">
                      <Award className="w-4 h-4" />
                      <span>Complete assessments and track progress</span>
                    </div>
                  </div>
                  <div className="mt-3 text-xs text-blue-600 bg-blue-100 px-3 py-2 rounded-md">
                    ✓ Instant access - no approval required
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
            
            <TabsContent value="Teacher" className="mt-4">
              <Card className="border-emerald-200 bg-emerald-50/50">
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg flex items-center gap-2 text-emerald-800">
                    <Users className="w-5 h-5" />
                    Teacher Account
                  </CardTitle>
                  <CardDescription className="text-emerald-700">
                    Create courses, manage students, and deliver educational content
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm text-emerald-700">
                      <BookOpen className="w-4 h-4" />
                      <span>Create and manage course content</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-emerald-700">
                      <Award className="w-4 h-4" />
                      <span>Design assessments and track student progress</span>
                    </div>
                  </div>
                  <div className="mt-3 text-xs text-amber-700 bg-amber-100 px-3 py-2 rounded-md border border-amber-200">
                    ⏳ Requires admin approval - account will be reviewed before activation
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </>
        )}
      </Tabs>
    </div>
  )
}
