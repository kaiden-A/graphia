import { NextResponse, type NextRequest } from "next/server";

const cookieName = process.env.SESSION_COOKIE_NAME ?? "graphia_session";

export default function proxy(request: NextRequest) {
  const hasSession = Boolean(request.cookies.get(cookieName)?.value);
  if (hasSession) {
    return NextResponse.next();
  }

  const url = request.nextUrl.clone();
  url.pathname = "/login";
  url.search = "";
  url.searchParams.set("next", `${request.nextUrl.pathname}${request.nextUrl.search}`);
  return NextResponse.redirect(url);
}

export const config = {
  matcher: ["/convert", "/conversions/:path*"],
};
