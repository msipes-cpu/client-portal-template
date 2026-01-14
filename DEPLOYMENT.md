# Deployment & Troubleshooting Guide

This project is deployed on **Railway**. The following rules and procedures are critical to maintain a stable environment and avoid connection/migration errors.

## 1. Database Provisioning (Critical)

**NEVER** create a "Service" and try to run a Postgres image manually or connect a "Postgres" repo.

**Correct Procedure:**
1.  In Railway, click the **New** button (or `Cmd + K`).
2.  Select **Database**.
3.  Select **PostgreSQL**.
4.  This provisions a managed database service (e.g., `PostgreSQL`, `Postgres-YnHD`).

**Why?**
Generic services run *code* (binding HTTP ports), not database engines. If you accidentally create a "Service" named Postgres, the app will fail with `HTTP 400` or `Received H` errors when trying to connect to it.

## 2. Environment Variables & Networking

Always use **Railway Internal Networking** for communication between the App and the Database.

**Correct Configuration:**
The `DATABASE_URL` in your Next.js App service should use the dynamic variable reference:
```
${{ Postgres.DATABASE_URL }}
```
*(Replace `Postgres` with the actual name of your database service, e.g., `${{ Postgres-YnHD.DATABASE_URL }}`)*

**Why?**
- **Speed:** Traffic stays within Railway's private network (AWS/GCP intranet).
- **Security:** No public internet exposure.
- **Reliability:** Avoids SSL handshake issues often seen with public proxies.

**Do NOT** hardcode values like `postgresql://postgres:password@roundhouse.proxy.rlwy.net...`.

## 3. Managing Migrations (Prisma)

Prisma's local migration history (`prisma/migrations`) must MATCH the remote database's history exactly.

### If you DELETE or RESET the Production Database:
1.  **Stop:** Do not try to deploy existing migrations.
2.  **Delete:** Remove your local `prisma/migrations` folder entirely.
3.  **Reset:** Run the following command locally (ensure you are connected to the remote DB via proxy, or use a local dev DB):
    ```bash
    # If connecting to remote via Proxy
    export DATABASE_URL="postgresql://...proxy..."
    npx prisma migrate dev --name init
    ```
4.  **Confirm:** This generates a new `init` migration that creates all tables from scratch.
5.  **Push:** Commit and push the new migration folder to GitHub.

**Why?**
If you deploy a fresh empty database but your code only has "Migration #2 (Add Column)" without "Migration #1 (Create Table)", deployment will fail with:
`Error: P3018 ... relation "Project" does not exist`.

## 4. Debugging Connection Issues

If the app fails to start with `P1001: Can't reach database server`:
1.  **Check Service Type:** Ensure the DB is a real Database service (see #1).
2.  **Check Variable:** Ensure `DATABASE_URL` is using `${{ ... }}` syntax.
3.  **Check Region:** Both App and DB should be in the same region (default: US West).
4.  **Avoid Debug Scripts:** Do not put blocking commands like `nc` or `nslookup` in the `CMD` chain in `Dockerfile`. If the internal network flakes, these will crash the boot loop.
