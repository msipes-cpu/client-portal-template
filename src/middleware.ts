import { NextRequest, NextResponse } from "next/server";

export const config = {
    matcher: [
        /*
         * Match all paths except for:
         * 1. /api routes
         * 2. /_next (Next.js internals)
         * 3. /_static (inside /public)
         * 4. all root files inside /public (e.g. /favicon.ico)
         */
        "/((?!api/|_next/|_static/|[\\w-]+\\.\\w+).*)",
    ],
};

export default async function middleware(req: NextRequest) {
    const url = req.nextUrl;
    const hostname = req.headers.get("host") || "";

    // Define allowed domains (including localhost for testing)
    // You might want to pull this from env vars in production
    const allowedDomains = ["localhost:3000", "client-portal-template.up.railway.app"];

    // Extract subdomain
    // e.g. "client.sipesautomation.com" -> "client"
    // e.g. "localhost:3000" -> null (or handle as root)
    const isLocal = hostname.includes("localhost");
    const rootDomain = isLocal ? "localhost:3000" : (process.env.NEXT_PUBLIC_ROOT_DOMAIN || "sipesautomation.com");

    // Check if we are on a subdomain
    const currentHost = hostname.replace(`.${rootDomain}`, "");

    // If no subdomain (main domain), or if it's one of the utility domains, serve root
    if (currentHost === rootDomain || currentHost === "www" || allowedDomains.some(d => hostname.includes(d))) {
        // You can let it pass through to standard /app/page.tsx logic or rewrite to a home page
        return NextResponse.next();
    }

    // If path already starts with /c/currentHost (e.g. via explicit link), 
    // we just rewrite to it directly effectively treating it as the internal path
    if (url.pathname.startsWith(`/c/${currentHost}`)) {
        return NextResponse.rewrite(url);
    }

    // Rewrite to the tenant path
    // e.g. client.sipesautomation.com/foo -> /c/client/foo
    return NextResponse.rewrite(new URL(`/c/${currentHost}${url.pathname}`, req.url));
}
