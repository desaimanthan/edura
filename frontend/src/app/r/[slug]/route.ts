import { NextResponse } from 'next/server';
import { redirectLinks, RedirectKey } from '@/config/redirects';

export async function GET(
  request: Request,
  { params }: { params: Promise<{ slug: string }> }
) {
  const resolvedParams = await params;
  const slug = resolvedParams.slug as RedirectKey;
  const redirectUrl = redirectLinks[slug];
  
  if (!redirectUrl) {
    // If no redirect URL is configured for this slug, return a 404
    return new NextResponse(`Redirect for '${slug}' not found`, { status: 404 });
  }
  
  // Perform the redirect
  return NextResponse.redirect(redirectUrl);
}
