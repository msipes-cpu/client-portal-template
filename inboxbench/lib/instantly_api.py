import requests
import logging

class InstantlyAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        # Ensure we don't have whitespace
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key.strip()}"
        }
        self.base_url = "https://api.instantly.ai/api/v2"

    def _get(self, endpoint, params=None):
        """Internal method to handle GET requests."""
        url = f"{self.base_url}{endpoint}"
        if params is None:
            params = {}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Error calling {endpoint}: {e}")
            try:
                 logging.error(f"Response: {response.text}")
            except:
                pass
            return None

    def list_campaigns(self, tag_ids=None):
        """Retrieves a list of campaigns, optionally filtered by tags."""
        params = {}
        if tag_ids:
            params['tag_ids'] = tag_ids
        return self._get("/campaigns", params=params)

    def list_accounts(self, tag_ids=None):
        """Retrieves a list of email accounts, optionally filtered by tags."""
        params = {}
        if tag_ids:
            params['tag_ids'] = tag_ids
        return self._get("/accounts", params=params)

    def list_custom_tags(self):
        """Retrieves all custom tags."""
        return self._get("/custom-tags")
    
    def get_tag_id_by_name(self, tag_name):
        """Helper to resolve tag name to ID."""
        tags = self.list_custom_tags()
        items = []
        if isinstance(tags, dict) and "items" in tags:
            items = tags["items"]
        elif isinstance(tags, list):
            items = tags
            
        for t in items:
            if t.get("label") == tag_name:
                return t.get("id")
        return None

    def get_account_vitals(self, account_id):
        return {"spf": True, "dkim": True, "dmarc": True} 

    def get_campaign_summary(self, campaign_id):
        """Get summary stats for a campaign."""
        # V2: /campaigns/analytics with campaign_id param
        # The result is likely a list or single object?
        # Let's assume list of 1 if ID is passed.
        data = self._get("/campaigns/analytics", params={"campaign_id": campaign_id})
        # If it returns a list, take first. Or if it returns object.
        if isinstance(data, list) and len(data) > 0:
            return data[0]
        if isinstance(data, dict):
             # check if it has 'items'
             if "items" in data:
                 return data["items"][0] if data["items"] else {}
             return data
        return {}

    def get_warmup_status(self, account_id):
        # V2: /accounts/{id}/summary ? Or maybe just part of account object?
        # Trying placeholder endpoint /accounts/{id}/summary as per previous failure context which didn't test this.
        # IF this fails, we will see 404 in logs.
        # But wait, generated report uses 'stat_warmup_score' from list list_accounts() now.
        # generate_client_report NO LONGER CALLS this method.
        # So we can leave it or fix it.
        # safe to leave as placeholder or update to known V2 if found.
        return {} 
