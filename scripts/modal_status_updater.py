import modal
import os
from supabase import create_client, Client

app = modal.App("agency-os-updater")

# Define image with dependencies
image = modal.Image.debian_slim().pip_install("supabase")

@app.function(image=image, secrets=[modal.Secret.from_name("supabase-secrets")])
def update_project_status(project_id: str, new_status: str, progress: int):
    # Retrieve secrets from Modal Environment
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")
    
    supabase: Client = create_client(url, key)
    
    # Update Supabase DB
    data, count = supabase.table('projects').update({
        "status": new_status, 
        "progress_percent": progress
    }).eq("id", project_id).execute()
    
    print(f"Updated Project {project_id} to {new_status} ({progress}%)")
    return data

@app.local_entrypoint()
def main():
    # Example Usage: run `modal run modal_status_updater.py`
    # This would be called by your Automation Pipeline when a milestone is hit.
    update_project_status.remote(
        project_id="sea-cow-123", 
        new_status="live", 
        progress=100
    )
