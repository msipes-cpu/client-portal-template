
import { NextResponse } from 'next/server';

export async function POST(request: Request) {
    try {
        const body = await request.json();

        // Use the backend URL from environment
        const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;

        if (!BACKEND_URL) {
            return NextResponse.json(
                { message: 'Backend URL not configured on server' },
                { status: 500 }
            );
        }

        const cleanUrl = BACKEND_URL.replace(/['"]/g, "").replace(/\/$/, "");
        const targetUrl = `${cleanUrl}/api/leads/process-url`;

        console.log(`[Proxy] Forwarding request to: ${targetUrl}`);

        const backendRes = await fetch(targetUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body),
        });

        const data = await backendRes.json();

        return NextResponse.json(data, { status: backendRes.status });

    } catch (error: any) {
        console.error("[Proxy] Error forwarding request:", error);
        return NextResponse.json(
            { message: error.message || 'Internal Proxy Error' },
            { status: 500 }
        );
    }
}
