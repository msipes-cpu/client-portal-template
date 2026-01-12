# Deployment Guide: Agency OS Stack

## 1. Database (Supabase)
1.  Create a new project at [database.new](https://database.new)
2.  Go to **SQL Editor** and run this query to create the table:
    ```sql
    create table projects (
      id text primary key,
      client_name text,
      project_name text,
      status text,
      progress_percent int,
      current_phase text,
      next_milestone text,
      last_updated text
    );
    
    -- Insert placeholder (Optional)
    insert into projects (id, client_name, project_name, status, progress_percent, current_phase, next_milestone, last_updated)
    values ('default', 'Client Name', 'New Project', 'planning', 0, 'Discovery', 'Kickoff', '2026-01-01');
    ```
3.  Go to **Project Settings > API** and copy the `Reference ID` and `anon key`.

## 2. Frontend (Vercel)
1.  Install Vercel CLI: `npm i -g vercel`
2.  Run `vercel login`
3.  Run `vercel` in this directory to deploy.
4.  **Environment Variables**: In Vercel Dashboard, add:
    - `NEXT_PUBLIC_SUPABASE_URL`: `https://[Reference ID].supabase.co`
    - `NEXT_PUBLIC_SUPABASE_ANON_KEY`: `[anon key]`

## 3. Operations (Modal)
*This controls the "Status Updates" from your backend.*
1.  Install Modal: `pip install modal`
2.  Setup Secrets: `modal secret create supabase-secrets SUPABASE_URL=... SUPABASE_KEY=...`
3.  Deploy the Updater: `modal deploy scripts/modal_status_updater.py`

## 4. Connecting it all
When your automation finishes a task (e.g., in n8n or Python), call the Modal function to update the Supabase DB. The Vercel frontend will reflect the new status instantly.
