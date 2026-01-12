
import { NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export async function GET(req: Request) {
    try {
        await prisma.$executeRaw`ALTER TABLE "Project" ADD COLUMN IF NOT EXISTS "share_email" TEXT;`;
        await prisma.$executeRaw`ALTER TABLE "Project" ADD COLUMN IF NOT EXISTS "report_email" TEXT;`;

        return NextResponse.json({ success: true, message: "Migration executed" });
    } catch (e) {
        console.error("Migration error:", e);
        return NextResponse.json({ success: false, error: String(e) }, { status: 500 });
    }
}
