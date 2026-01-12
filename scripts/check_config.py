import sys
import os
from prisma import Prisma
import asyncio

async def main():
    try:
        db = Prisma()
        await db.connect()
        
        # Fetch all projects
        projects = await db.project.find_many()
        print(f"Found {len(projects)} projects.")
        
        for p in projects:
            print(f"--- Domain: {p.subdomain} ---")
            print(f"Sheet URL: {p.google_sheet_url}")
            print(f"Report Email: {p.report_email}")
            print(f"Share Email: {p.share_email}")
            print("-----------------------------")
            
        await db.disconnect()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
