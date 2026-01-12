import { NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';
import { z } from 'zod';

const prisma = new PrismaClient();

const configSchema = z.object({
    instantlyApiKey: z.string().optional(),
    googleSheetUrl: z.string().optional(),
});

// GET: Fetch config for a project by subdomain
export async function GET(request: Request) {
    try {
        const url = new URL(request.url);
        // Domain might be passed as query param if not using dynamic route here, 
        // but the file path suggests it's likely a generic route. 
        // Let's assume the client sends domain in searchParams for now as it's cleaner than dynamic API route just for this.
        const domain = url.searchParams.get('domain');

        if (!domain) {
            return NextResponse.json({ error: 'Domain is required' }, { status: 400 });
        }

        const project = await prisma.project.findUnique({
            where: { subdomain: domain },
            select: { instantly_api_key: true, google_sheet_url: true }
        });

        if (!project) {
            return NextResponse.json({ error: 'Project not found' }, { status: 404 });
        }

        // Mask the key for security, only showing last 4? Or send full if user needs it?
        // User wants "persistence", usually inputs show the key or valid state. 
        // Sending masked might be better: "••••••••••••1234"
        // BUT user asked "Do I have to put them in every single time?", implies standard password field behavior.
        // Let's send it back. It's over HTTPS. 
        return NextResponse.json({
            instantlyApiKey: project.instantly_api_key || '',
            googleSheetUrl: project.google_sheet_url || ''
        });

    } catch (error) {
        console.error('Error fetching config:', error);
        return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
    }
}

// POST: Update config
export async function POST(request: Request) {
    try {
        const body = await request.json();
        const { domain, instantlyApiKey, googleSheetUrl } = body;

        if (!domain) {
            return NextResponse.json({ error: 'Domain is required' }, { status: 400 });
        }

        const updateData: any = {};
        if (instantlyApiKey !== undefined) updateData.instantly_api_key = instantlyApiKey;
        if (googleSheetUrl !== undefined) updateData.google_sheet_url = googleSheetUrl;

        await prisma.project.update({
            where: { subdomain: domain },
            data: updateData
        });

        return NextResponse.json({ success: true });

    } catch (error) {
        console.error('Error updating config:', error);
        return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
    }
}
