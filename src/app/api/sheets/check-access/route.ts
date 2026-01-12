import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';
import util from 'util';

const execAsync = util.promisify(exec);

export async function POST(req: Request) {
    try {
        const { sheetUrl } = await req.json();

        if (!sheetUrl) {
            return NextResponse.json({ success: false, error: "URL is required" }, { status: 400 });
        }

        const scriptPath = path.join(process.cwd(), 'inboxbench/execution/check_sheet_access.py');
        const cleanUrl = sheetUrl.replace(/["']/g, ""); # Basic sanitization

        const command = `python3 "${scriptPath}" --url "${cleanUrl}"`;

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
