import os
from supabase import create_client, Client

# Credentials provided by user
url = "https://yrelzghzqxlwlslgkgnd.supabase.co"
key = "sb_publishable_VXCIf6QGfDp4ANKl9Ub1ow_oQ0ss3VZ"

def init_db():
    print(f"Connecting to Supabase at {url}...")
    try:
        supabase: Client = create_client(url, key)
        
        # 1. Create Table (Using SQL via RPC or just checking connection)
        # Supabase-js/py doesn't support 'create table' directly on client usually, 
        # unless we use rpc. But we can try to insert a row to see if it works 
        # (assuming user ran the SQL in the dashboard as per guide). 
        # OR, since the user gave us the keys, maybe they haven't run the SQL yet?
        # The Guide said "Go to SQL Editor and run query". 
        # Let's try to Select from 'projects'. If it errors 'relation does not exist', 
        # then we know they didn't run the SQL.
        
        print("Checking for 'projects' table...")
        response = supabase.table("projects").select("*").limit(1).execute()
        print("Connection Successful!")
        print(f"Data: {response}")
        
    except Exception as e:
        print(f"FAILED to connect or query: {e}")

if __name__ == "__main__":
    init_db()
