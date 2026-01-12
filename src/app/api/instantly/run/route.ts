import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';
import util from 'util';

const execAsync = util.promisify(exec);

export async function POST(req: Request) {
    try {
        const { token, sheetUrl, reportEmail } = await req.json();

        if (!token) {
            return NextResponse.json({ success: false, error: "Token is required" }, { status: 400 });
        }

        // Path to the python script
        const scriptPath = path.join(process.cwd(), 'inboxbench/execution/run_adhoc_workflow.py');

        // Sanitize
        if (/[^a-zA-Z0-9\-\_\=\:\.]/.test(token)) {
            return NextResponse.json({ success: false, error: "Invalid characters in token" }, { status: 400 });
        }

        let command = `python3 "${scriptPath}" --key "${token}"`;
        if (sheetUrl) {
            // Basic sanitation for URL (remove quotes)
            const cleanUrl = sheetUrl.replace(/["']/g, "");
            command += ` --sheet "${cleanUrl}"`;
        }
        if (reportEmail) {
            const cleanEmail = reportEmail.replace(/["' ]/g, "");
            command += ` --report_email "${cleanEmail}"`;
        }

        const { stdout, stderr } = await execAsync(command);

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
