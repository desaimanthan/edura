'use client';

import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { authService } from '@/lib/auth';

function AuthCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');

  useEffect(() => {
    const handleCallback = async () => {
      try {
        const token = searchParams.get('token');
        const userId = searchParams.get('user_id');
        const error = searchParams.get('error');
        const role = searchParams.get('role');

        console.log('🔍 OAuth Callback Debug - Starting callback handling');
        console.log('🔍 OAuth Callback Debug - Token:', token ? 'present' : 'missing');
        console.log('🔍 OAuth Callback Debug - User ID:', userId);
        console.log('🔍 OAuth Callback Debug - Role:', role);
        console.log('🔍 OAuth Callback Debug - Error:', error);

        if (error) {
          setStatus('error');
          setTimeout(() => {
            router.push('/auth/signin?error=oauth_failed');
          }, 2000);
          return;
        }

        if (token && userId) {
          console.log('🔍 OAuth Callback Debug - Processing successful OAuth callback');
          
          try {
            const user = await authService.handleAuthCallback(token, userId);
            console.log('🔍 OAuth Callback Debug - Auth callback completed successfully');
            console.log('🔍 OAuth Callback Debug - User active status:', user?.is_active);
            
            setStatus('success');
            setTimeout(() => {
              // Always redirect to dashboard - let dashboard handle pending approval status
              router.push('/dashboard');
            }, 1000);
          } catch (authError) {
            console.error('🔍 OAuth Callback Debug - Auth callback error:', authError);
            // If it's a "Failed to fetch user data" error, it might be because the user is inactive
            if (authError instanceof Error && authError.message.includes('Failed to fetch user data')) {
              // This is likely a Teacher account pending approval - still redirect to dashboard
              setStatus('success');
              setTimeout(() => {
                router.push('/dashboard');
              }, 1000);
              return;
            }
            throw authError;
          }
        } else {
          setStatus('error');
          setTimeout(() => {
            router.push('/auth/signin?error=invalid_callback');
          }, 2000);
        }
      } catch (error) {
        console.error('🔍 OAuth Callback Debug - Callback error:', error);
        setStatus('error');
        setTimeout(() => {
          router.push('/auth/signin?error=callback_failed');
        }, 2000);
      }
    };

    handleCallback();
  }, [searchParams, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          {status === 'loading' && (
            <>
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mx-auto"></div>
              <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
                Completing sign in...
              </h2>
              <p className="mt-2 text-sm text-gray-600">
                Please wait while we complete your authentication.
              </p>
            </>
          )}
          
          {status === 'success' && (
            <>
              <div className="rounded-full h-12 w-12 bg-green-100 mx-auto flex items-center justify-center">
                <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                </svg>
              </div>
              <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
                Success!
              </h2>
              <p className="mt-2 text-sm text-gray-600">
                Redirecting to your dashboard...
              </p>
            </>
          )}
          
          {status === 'error' && (
            <>
              <div className="rounded-full h-12 w-12 bg-red-100 mx-auto flex items-center justify-center">
                <svg className="h-6 w-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
              </div>
              <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
                Authentication Failed
              </h2>
              <p className="mt-2 text-sm text-gray-600">
                Redirecting to sign in page...
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default function AuthCallback() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
      </div>
    }>
      <AuthCallbackContent />
    </Suspense>
  );
}
