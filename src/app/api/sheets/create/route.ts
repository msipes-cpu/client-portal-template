import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';
import util from 'util';

const execAsync = util.promisify(exec);

export async function POST(req: Request) {
    try {
        const { title, shareEmail } = await req.json();
        const safeTitle = (title || "InboxBench Report").replace(/[^a-zA-Z0-9 \-_]/g, "");

        const scriptPath = path.join(process.cwd(), 'inboxbench/execution/create_client_sheet.py');

        let command = `python3 "${scriptPath}" --title "${safeTitle}"`;
        if (shareEmail) {
            const cleanEmail = shareEmail.replace(/["' ]/g, "");
            command += ` --share_email "${cleanEmail}"`;
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
