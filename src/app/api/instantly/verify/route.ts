import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';
import util from 'util';

import { PrismaClient } from '@prisma/client';
const execAsync = util.promisify(exec);

const prisma = new PrismaClient();

// GET: Fetch config (Hijacked)
export async function GET(req: Request) {
    try {
        const url = new URL(req.url);
        const domain = url.searchParams.get('domain');
        if (!domain) return NextResponse.json({ error: 'Domain required' }, { status: 400 });

        const project = await prisma.project.findUnique({
            where: { subdomain: domain },
            select: { instantly_api_key: true, google_sheet_url: true, share_email: true, report_email: true }
        });

        // If no project, return empty (standard behavior for this UI)
        return NextResponse.json({
            instantlyApiKey: project?.instantly_api_key || '',
            googleSheetUrl: project?.google_sheet_url || '',
            shareEmail: project?.share_email || '',
            reportEmail: project?.report_email || '',
            runTime: project?.run_time || ''
        });
    } catch (e) {
        console.error("GET /api/instantly/verify error:", e);
        return NextResponse.json({ error: 'Fetch error', details: String(e) }, { status: 500 });
    }
}

// PUT: Save config (Hijacked)
export async function PUT(req: Request) {
    try {
        const body = await req.json();
        const { domain, instantlyApiKey, googleSheetUrl, shareEmail, reportEmail, runTime } = body;
        if (!domain) return NextResponse.json({ error: 'Domain required' }, { status: 400 });

        const updateData: any = {};
        if (instantlyApiKey !== undefined) updateData.instantly_api_key = instantlyApiKey;
        if (googleSheetUrl !== undefined) updateData.google_sheet_url = googleSheetUrl;
        if (shareEmail !== undefined) updateData.share_email = shareEmail;
        if (reportEmail !== undefined) updateData.report_email = reportEmail;
        if (runTime !== undefined) updateData.run_time = runTime;

        // Upsert ensures the project exists even if not seeded
        await prisma.project.upsert({
            where: { subdomain: domain },
            update: updateData,
            create: {
                subdomain: domain,
                client_name: domain.charAt(0).toUpperCase() + domain.slice(1), // Fallback name
                project_name: "Verification Project",
                status: "active",
                progress_percent: 0,
                current_phase: "setup",
                next_milestone: "init",
                last_updated: new Date().toISOString(),
                instantly_api_key: instantlyApiKey || '',
                google_sheet_url: googleSheetUrl || '',
                share_email: shareEmail || '',
                report_email: reportEmail || '',
                run_time: runTime || '',
                ...updateData
            }
        });

        return NextResponse.json({ success: true });
    } catch (e) {
        console.error("Config save error:", e);
        return NextResponse.json({ error: 'Update error' }, { status: 500 });
    }
}

export async function POST(req: Request) {
    // ... existing POST logic ...
    // ... existing POST logic ...
    try {
        const { token } = await req.json();

        if (!token) {
            return NextResponse.json({ success: false, error: "Token is required" }, { status: 400 });
        }

        // Resolve path dynamically to work in both local and Docker environments
        const scriptPath = path.join(process.cwd(), 'inboxbench/execution/verify_workspace.py');

        // Sanitize token to be safe for command line (basic check)
        if (/[^a-zA-Z0-9\-\_\=\:\.]/.test(token)) {
            return NextResponse.json({ success: false, error: "Invalid characters in token" }, { status: 400 });
        }

        const { stdout, stderr } = await execAsync(`python3 "${scriptPath}" --key "${token}"`);

        // Parse the JSON output from stdout
        try {
            const result = JSON.parse(stdout.trim());
            return NextResponse.json(result);
        } catch (parseError) {
            console.error("Parse Error:", stdout);
            return NextResponse.json({
                success: false,
                error: "Failed to parse script output",
                details: stdout,
                stderr: stderr
            }, { status: 500 });
        }

    } catch (error: any) {
        return NextResponse.json({
            success: false,
            error: error.message
        }, { status: 500 });
    }
}
