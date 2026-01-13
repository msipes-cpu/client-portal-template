import { NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';

export async function POST(req: Request) {
    try {
        const { token, sheetUrl, reportEmail, warmupThreshold, benchPercent } = await req.json();

        if (!token) {
            return NextResponse.json({ success: false, error: "Token is required" }, { status: 400 });
        }

        // Path to the python script
        const scriptPath = path.join(process.cwd(), 'inboxbench/execution/run_adhoc_workflow.py');

        // Sanitize
        if (/[^a-zA-Z0-9\-\_\=\:\.]/.test(token)) {
            return NextResponse.json({ success: false, error: "Invalid characters in token" }, { status: 400 });
        }

        const args = ["-u", scriptPath, "--key", token]; // -u for unbuffered python output
        if (sheetUrl) {
            const cleanUrl = sheetUrl.replace(/["']/g, "");
            args.push("--sheet", cleanUrl);
        }
        if (reportEmail) {
            const cleanEmail = reportEmail.replace(/["' ]/g, "");
            args.push("--report_email", cleanEmail);
        }
        if (warmupThreshold) {
            args.push("--warmup_threshold", String(warmupThreshold));
        }
        if (typeof benchPercent !== 'undefined') {
            args.push("--bench_percent", String(benchPercent));
        }

        const encoder = new TextEncoder();

        const stream = new ReadableStream({
            start(controller) {
                const child = spawn('python3', args);

                child.stdout.on('data', (data) => {
                    controller.enqueue(data);
                });

                child.stderr.on('data', (data) => {
                    console.error(`[Python Stderr]: ${data}`);
                });

                child.on('close', (code) => {
                    if (code !== 0) {
                        console.error(`Process exited with code ${code}`);
                        const exitMsg = JSON.stringify({ type: "error", message: `Process exited with code ${code}` });
                        controller.enqueue(encoder.encode(exitMsg + "\n"));
                    }
                    controller.close();
                });

                child.on('error', (err) => {
                    console.error("Spawn Error:", err);
                    const errMsg = JSON.stringify({ type: "error", message: "Spawn Failed: " + err.message });
                    controller.enqueue(encoder.encode(errMsg + "\n"));
                    controller.close();
                });
            }
        });

        return new Response(stream, {
            headers: {
                'Content-Type': 'text/plain; charset=utf-8',
                'X-Content-Type-Options': 'nosniff',
            },
        });

    } catch (error: any) {
        return NextResponse.json({
            success: false,
            error: error.message
        }, { status: 500 });
    }
}
