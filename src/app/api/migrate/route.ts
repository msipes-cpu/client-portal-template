import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import util from 'util';

const execAsync = util.promisify(exec);

export const dynamic = 'force-dynamic';

export async function GET() {
    try {
        // Run the global prisma command we installed
        const { stdout, stderr } = await execAsync('prisma db push --skip-generate');
        return NextResponse.json({
            success: true,
            output: stdout,
            error: stderr
        });
    } catch (error: any) {
        return NextResponse.json({
            success: false,
            error: error.message,
            details: String(error)
        }, { status: 500 });
    }
}
