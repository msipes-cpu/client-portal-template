
import { NextResponse } from 'next/server';

const getBackendUrl = () => {
    const raw = process.env.NEXT_PUBLIC_BACKEND_URL || "";
    return raw.replace(/['"]/g, "").replace(/\/$/, "");
}

export async function GET(request: Request) {
    const { searchParams } = new URL(request.url);
    const path = searchParams.get('path');

    if (!path) {
        return NextResponse.json({ message: 'Missing path param' }, { status: 400 });
    }

    const backendUrl = getBackendUrl();
    if (!backendUrl) {
        return NextResponse.json({ message: 'Backend URL not configured' }, { status: 500 });
    }

    const targetUrl = `${backendUrl}${path}`;

    try {
        const res = await fetch(targetUrl);
        const data = await res.json();
        return NextResponse.json(data, { status: res.status });
    } catch (error: any) {
        return NextResponse.json({ message: error.message }, { status: 500 });
    }
}

export async function POST(request: Request) {
    let targetUrl = "";
    try {
        const body = await request.json();
        const backendUrl = getBackendUrl();

        if (!backendUrl) {
            return NextResponse.json({ message: 'Backend URL not configured' }, { status: 500 });
        }

        // Default to lead process if no path provided (backward compatibility)
        // Or we can expect the frontend to pass the path in the body/query?
        // For now, let's keep the hardcoded default for the existing POST implementation
        // but cleaner.
        targetUrl = `${backendUrl}/api/leads/process-url`;

        console.log(`[Proxy] Forwarding request to: ${targetUrl}`);

        const backendRes = await fetch(targetUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });

        const data = await backendRes.json();
        return NextResponse.json(data, { status: backendRes.status });

    } catch (error: any) {
        console.error("[Proxy] Error forwarding request:", error);
        return NextResponse.json(
            {
                message: error.message || 'Internal Proxy Error',
                debug_url: targetUrl,
                cause: error.cause ? String(error.cause) : undefined,
                code: error.code
            },
            { status: 500 }
        );
    }
}
