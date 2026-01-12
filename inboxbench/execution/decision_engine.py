import logging
from datetime import datetime, timedelta

# Constants for Rules
MIN_AGE_DAYS = 14
ROTATION_DAYS = 14
BENCH_REST_DAYS = 7
SICK_MAX_DAYS = 30

WARMUP_INBOX_MIN = 70.0 #%
WARMUP_RECOVERY_MIN = 85.0 #%
WARMUP_ACTIVE_MIN = 90.0 #%

# Tags
TAG_STATUS_ACTIVE = "status-active"
TAG_STATUS_WARMING = "status-warming"
TAG_STATUS_BENCHED = "status-benched"
TAG_STATUS_SICK = "status-sick"
TAG_STATUS_DEAD = "status-dead"

class DecisionEngine:
    def __init__(self, api):
        self.api = api
        self.actions_log = []

    def evaluate_account(self, account, analytics=None):
        """
        Runs the 7-Rule Check on a single account.
        Returns a dict of actions to take.
        """
        email = account.get("email")
        created_at_str = account.get("timestamp_created")
        current_tags = account.get("tags_resolved", []) # List of tag names
        
        # Parse Dates
        created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
        age_days = (datetime.now(created_at.tzinfo) - created_at).days

        # Analytics (Fallback if missing)
        inbox_rate = analytics.get("inbox_rate", 100.0) if analytics else 100.0
        # If we rely on score:
        warmup_score = int(account.get("stat_warmup_score", 0))

        # Auth Status (Mocked/Placeholder until deep fetch works)
        # Assume valid unless api says otherwise
        auth_valid = True 

        # Current Status Tag
        status_tag = self._get_status_tag(current_tags)
        
        logging.info(f"Evaluating {email} | Age: {age_days}d | Status: {status_tag} | Score: {warmup_score}")

        # --- RULE 1: New Account Check ---
        if age_days < MIN_AGE_DAYS:
            if status_tag != TAG_STATUS_WARMING:
                return self._create_action(email, "Rule 1: New Account (<14 days)", TAG_STATUS_WARMING, warmup=True, campaigns="REMOVE")
            return None # No change needed

        # --- RULE 2: Auth Check ---
        if not auth_valid:
             if status_tag != TAG_STATUS_SICK:
                return self._create_action(email, "Rule 2: Auth Invalid", TAG_STATUS_SICK, warmup=False, campaigns="REMOVE")
             return None

        # --- RULE 3: Warmup Health Check ---
        # Using Warmup Score as proxy for now since API doesn't give rates easily
        # 100 score ~= good rates. <70 score ~= bad.
        if warmup_score < 70:
            if status_tag != TAG_STATUS_SICK:
                 return self._create_action(email, f"Rule 3: Low Health Score ({warmup_score})", TAG_STATUS_SICK, warmup=True, campaigns="REMOVE")
            return None

        # --- RULE 4: Warmup Recovery Check ---
        if status_tag == TAG_STATUS_SICK:
            # Check if recovered. Requires history which we don't have easily yet.
            # Simplified: If score is perfect now, move to BENCHED
            if warmup_score > 95:
                 return self._create_action(email, "Rule 4: Recovered (Score > 95)", TAG_STATUS_BENCHED, warmup=True, campaigns="REMOVE")
            return None

        # --- RULE 5: Bench Rotation Check ---
        if status_tag == TAG_STATUS_ACTIVE:
            # How long active? Need history.
            # Simplified: Random/Time check?
            # For MVP: If age > 14 days and we don't have granular "days in status", skip for now.
            # OR logic: if created > 14 days ago and TAG is active... wait, removing active accounts just by age is wrong.
            # We need "Days in Status". Since we don't track that yet without DB,
            # We will SKIP Rule 5 in V1.
            pass

        # --- RULE 6: Return to Active Check ---
        if status_tag == TAG_STATUS_BENCHED:
            # If healthy, bring back.
            if warmup_score >= 90:
                 return self._create_action(email, "Rule 6: Rested & Healthy", TAG_STATUS_ACTIVE, warmup=True, campaigns="ADD")
            return None

        # --- RULE 7: Dead Account Check ---
        if status_tag == TAG_STATUS_SICK:
             # Need "Days in Sick". Skip for V1.
             pass
        
        # Default: If no status tag, set to Active if old enough
        if not status_tag and age_days >= MIN_AGE_DAYS:
             return self._create_action(email, "Rule 0: Unlabeled -> Active", TAG_STATUS_ACTIVE, warmup=True, campaigns="ADD")

        return None

    def _get_status_tag(self, tags):
        for t in tags:
            if t.startswith("status-"):
                return t
        return None

    def _create_action(self, email, reason, new_tag, warmup=None, campaigns=None):
        return {
            "email": email,
            "reason": reason,
            "new_tag": new_tag,
            "warmup": warmup, # True/False/None
            "campaigns": campaigns # "REMOVE", "ADD", None
        }
