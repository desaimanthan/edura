'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/components/providers/auth-provider';

interface RouteGuardProps {
  children: React.ReactNode;
  requiresApproval?: boolean;
  allowedRoles?: string[];
}

export function RouteGuard({ 
  children, 
  requiresApproval = false,
  allowedRoles = []
}: RouteGuardProps) {
  const { user, loading, isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (loading) return; // Still loading, don't redirect yet

    // Check if user is authenticated
    if (!isAuthenticated) {
      router.push('/auth/signin');
      return;
    }

    // Check role-based access first
    if (allowedRoles.length > 0 && user?.role_name) {
      if (!allowedRoles.includes(user.role_name)) {
        router.push('/dashboard'); // Redirect to dashboard if role not allowed
        return;
      }
    }

    // Check approval status for teachers accessing routes that require approval
    if (requiresApproval && user?.role_name === 'Teacher' && user?.approval_status === 'pending') {
      router.push('/dashboard'); // Redirect pending teachers to dashboard
      return;
    }
  }, [user, loading, isAuthenticated, router, requiresApproval, allowedRoles]);

  // Show loading while checking authentication
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  // Don't render if not authenticated (will redirect)
  if (!isAuthenticated) {
    return null;
  }

  // Don't render if role not allowed
  if (allowedRoles.length > 0 && user?.role_name && !allowedRoles.includes(user.role_name)) {
    return null;
  }

  // Don't render if teacher is pending approval for restricted routes
  if (requiresApproval && user?.role_name === 'Teacher' && user?.approval_status === 'pending') {
    return null;
  }

  return <>{children}</>;
}
