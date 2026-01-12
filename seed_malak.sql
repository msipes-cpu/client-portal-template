-- Run this query in your Railway Postgres Database (Data Tab -> SQL Query)

INSERT INTO "Project" (
  id, 
  subdomain, 
  client_name, 
  project_name, 
  status, 
  progress_percent, 
  current_phase, 
  next_milestone, 
  last_updated, 
  blueprint_path, 
  created_at, 
  updated_at
)
VALUES (
  gen_random_uuid(),
  'malak', 
  'Malak', 
  'Automation Implementation', 
  'planning', 
  10, 
  'Discovery & Strategy', 
  'Blueprint Presentation', 
  '2026-01-11', 
  '/malak-blueprint', 
  NOW(), 
  NOW()
) ON CONFLICT (subdomain) DO NOTHING;

-- Verify it worked
SELECT * FROM "Project" WHERE subdomain = 'malak';
