const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();

async function main() {
    const subdomain = 'malak';

    console.log(`Checking if project '${subdomain}' exists...`);

    const existing = await prisma.project.findUnique({
        where: { subdomain },
    });

    if (existing) {
        console.log(`Project '${subdomain}' already exists.`);
        return;
    }

    console.log(`Creating project for '${subdomain}'...`);

    await prisma.project.create({
        data: {
            subdomain: subdomain,
            client_name: "Malak",
            project_name: "Automation Implementation",
            status: "planning",
            progress_percent: 10,
            current_phase: "Discovery & Strategy",
            next_milestone: "Blueprint Presentation",
            last_updated: new Date().toISOString().split('T')[0],
            blueprint_path: "/malak-blueprint"
        }
    });

    console.log(`Successfully created project for 'Malak' at 'malak.sipesautomation.com'`);
}

main()
    .catch((e) => {
        console.error(e);
        process.exit(1);
    })
    .finally(async () => {
        await prisma.$disconnect();
    });
