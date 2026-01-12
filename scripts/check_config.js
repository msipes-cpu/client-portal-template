const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();

async function main() {
    try {
        const projects = await prisma.project.findMany();
        console.log(`Found ${projects.length} projects.`);

        projects.forEach(p => {
            console.log(`--- Domain: ${p.subdomain} ---`);
            console.log(`Sheet URL: ${p.google_sheet_url}`);
            console.log(`Report Email: ${p.report_email}`);
            console.log(`Share Email: ${p.share_email}`);
            console.log("-----------------------------");
        });
    } catch (e) {
        console.error("Error:", e);
    } finally {
        await prisma.$disconnect();
    }
}

main();
