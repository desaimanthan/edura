import { NextResponse } from 'next/server';
import { redirectLinks } from '@/config/redirects';

export async function GET() {
  const redirectUrl = redirectLinks['video-demo'];
  
  if (!redirectUrl) {
    // If no redirect URL is configured, return a 404
    return new NextResponse('Redirect not found', { status: 404 });
  }
  
  // Perform the redirect
  return NextResponse.redirect(redirectUrl);
}
