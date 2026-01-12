import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';
import util from 'util';

const execAsync = util.promisify(exec);

export async function POST(req: Request) {
    try {
        const { apiKey } = await req.json();

        // Simple protection
        if (apiKey !== "sipes-diag") {
            return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
        }

        const scriptPath = path.join(process.cwd(), 'inboxbench/execution/debug_creds.py');
        const command = `python3 "${scriptPath}"`;

        const { stdout, stderr } = await execAsync(command);

        return NextResponse.json({
            stdout,
            stderr
        });

    } catch (error: any) {
        return NextResponse.json({
            success: false,
            error: error.message
        }, { status: 500 });
    }
}
