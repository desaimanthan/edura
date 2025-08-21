"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { useAuth } from "@/components/providers/auth-provider";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { RouteGuard } from "@/components/auth/route-guard";
import { Settings, Shield, Users, Loader2, Sliders } from "lucide-react";
import { API_BASE_URL, logApiCall } from "@/lib/api-config";
import { authService } from "@/lib/auth";

interface SystemSetting {
  id: string;
  setting_key: string;
  setting_value: boolean | string | number;
  setting_type: string;
  description: string;
  updated_by?: string;
  updated_at: string;
  created_at: string;
}

export default function SettingsPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [teacherApprovalRequired, setTeacherApprovalRequired] = useState(true);
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const token = authService.getToken();
      const url = `${API_BASE_URL}/settings/teacher_approval_required`;
      
      logApiCall('GET', url);
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data: SystemSetting = await response.json();
        setTeacherApprovalRequired(Boolean(data.setting_value));
        setInitialized(true);
      } else if (response.status === 404) {
        // Setting doesn't exist, initialize it
        await initializeSettings();
      } else {
        const errorText = await response.text();
        console.error("Error response:", errorText);
        toast.error(`Failed to load settings: ${response.status}`);
      }
    } catch (error) {
      console.error("Error fetching settings:", error);
      toast.error(`Failed to load settings: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  const initializeSettings = async () => {
    try {
      const token = authService.getToken();
      const url = `${API_BASE_URL}/settings/initialize`;
      
      logApiCall('POST', url);
      
      const response = await fetch(url, {
        method: "POST",
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        toast.success("Settings initialized successfully");
        setTeacherApprovalRequired(true); // Default value
        setInitialized(true);
      } else {
        const errorText = await response.text();
        console.error("Error response:", errorText);
        toast.error(`Failed to initialize settings: ${response.status}`);
      }
    } catch (error) {
      console.error("Error initializing settings:", error);
      toast.error(`Failed to initialize settings: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const handleToggleTeacherApproval = async (checked: boolean) => {
    try {
      setSaving(true);
      setTeacherApprovalRequired(checked);

      const token = authService.getToken();
      const url = `${API_BASE_URL}/settings/teacher_approval_required`;
      const body = JSON.stringify({
        setting_value: checked,
      });
      
      logApiCall('PUT', url, { setting_value: checked });
      
      const response = await fetch(url, {
        method: "PUT",
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: body,
      });

      if (response.ok) {
        toast.success(
          checked
            ? "Teacher approval flow enabled. New teacher accounts will require admin approval."
            : "Teacher approval flow disabled. New teacher accounts will be automatically approved."
        );
      } else {
        // Revert the change if the update failed
        setTeacherApprovalRequired(!checked);
        const errorText = await response.text();
        console.error("Error response:", errorText);
        toast.error(`Failed to update setting: ${response.status}`);
      }
    } catch (error) {
      console.error("Error updating setting:", error);
      setTeacherApprovalRequired(!checked);
      toast.error(`Failed to update setting: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <DashboardLayout 
        title="System Settings" 
        icon={Sliders}
        showBackButton={true}
        backUrl="/masters"
        backLabel="Back to Masters"
      >
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
            <p className="mt-2 text-sm text-muted-foreground">Loading settings...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <RouteGuard allowedRoles={["Administrator"]}>
      <DashboardLayout 
        title="System Settings" 
        icon={Sliders}
        showBackButton={true}
        backUrl="/masters"
        backLabel="Back to Masters"
      >
        <div className="grid gap-6">
        {/* Teacher Approval Settings */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-primary" />
              <CardTitle>Teacher Approval Settings</CardTitle>
            </div>
            <CardDescription>
              Configure how teacher accounts are approved in the system
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center justify-between space-x-4">
              <div className="flex-1 space-y-1">
                <Label htmlFor="teacher-approval" className="text-base font-medium">
                  Require Admin Approval for Teachers
                </Label>
                <p className="text-sm text-muted-foreground">
                  When enabled, new teacher accounts will need to be manually approved by an administrator
                  before they can access the system. When disabled, teacher accounts are automatically
                  approved upon registration.
                </p>
              </div>
              <Switch
                id="teacher-approval"
                checked={teacherApprovalRequired}
                onCheckedChange={handleToggleTeacherApproval}
                disabled={saving}
                aria-label="Toggle teacher approval requirement"
              />
            </div>

            {/* Status Indicator */}
            <div className="rounded-lg border p-4 bg-muted/50">
              <div className="flex items-center gap-2">
                <Users className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium">Current Status:</span>
                <span
                  className={`text-sm font-semibold ${
                    teacherApprovalRequired ? "text-orange-600" : "text-green-600"
                  }`}
                >
                  {teacherApprovalRequired
                    ? "Manual Approval Required"
                    : "Automatic Approval Enabled"}
                </span>
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                {teacherApprovalRequired
                  ? "New teacher registrations will be placed in a pending state until approved by an admin."
                  : "New teacher registrations will be automatically approved and can immediately access the system."}
              </p>
            </div>

            {/* Additional Information */}
            <div className="text-sm text-muted-foreground space-y-2">
              <p className="font-medium">Note:</p>
              <ul className="list-disc list-inside space-y-1">
                <li>This setting only affects new teacher registrations</li>
                <li>Existing teacher accounts will not be affected by this change</li>
                <li>Student accounts are always automatically approved regardless of this setting</li>
                <li>
                  {teacherApprovalRequired
                    ? "You can view and manage pending teacher approvals in the Users section"
                    : "Teachers will have immediate access to create and manage courses"}
                </li>
              </ul>
            </div>
          </CardContent>
        </Card>

          {/* Future Settings Cards can be added here */}
        </div>
      </DashboardLayout>
    </RouteGuard>
  );
}
