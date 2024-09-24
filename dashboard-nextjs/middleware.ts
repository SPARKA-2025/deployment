import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { setCookie } from 'cookies-next';

// Define the paths that should not be restricted
const PUBLIC_PATHS = ['/', '/login', '/register', '/api'];

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  // Allow the public paths without checking for the token
  if (PUBLIC_PATHS.includes(pathname)) {
    return NextResponse.next();
  }

  // Check if the token exists in the cookies
  const token = req.cookies.get('access-token');

  // If the token does not exist, redirect to the login page
  if (!token) {
    return NextResponse.redirect(new URL('/login', req.url));
  }

  // If the token exists, allow the request
  return NextResponse.next();
}

// Match all routes (with an optional static file)
export const config = {
  matcher: '/((?!api|_next/static|_next/image|favicon.ico|sitemap.xml|robots.txt).*)',
};
