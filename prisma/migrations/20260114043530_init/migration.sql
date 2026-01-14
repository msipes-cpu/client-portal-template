-- CreateTable
CREATE TABLE "Project" (
    "id" TEXT NOT NULL,
    "subdomain" TEXT NOT NULL,
    "client_name" TEXT NOT NULL,
    "project_name" TEXT NOT NULL,
    "status" TEXT NOT NULL,
    "progress_percent" INTEGER NOT NULL,
    "current_phase" TEXT NOT NULL,
    "next_milestone" TEXT NOT NULL,
    "last_updated" TEXT NOT NULL,
    "blueprint_path" TEXT,
    "instantly_api_key" TEXT,
    "google_sheet_url" TEXT,
    "share_email" TEXT,
    "report_email" TEXT,
    "run_time" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Project_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "Project_subdomain_key" ON "Project"("subdomain");
