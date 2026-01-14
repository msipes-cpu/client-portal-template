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
TAG_STATUS_SENDING = "Sending"
TAG_STATUS_WARMING = "Warming"
TAG_STATUS_BENCHED = "Benched"
TAG_STATUS_SICK = "Sick"

STATUS_TAGS = {TAG_STATUS_SENDING, TAG_STATUS_WARMING, TAG_STATUS_BENCHED, TAG_STATUS_SICK}

class DecisionEngine:
    def __init__(self, api, config=None):
        self.api = api
        self.config = config or {}
        self.actions_log = []

    def evaluate_account(self, account, analytics=None, force_status=None):
        """
        Runs the 7-Rule Check on a single account.
        Returns a dict of actions to take.
        """
        email = account.get("email")
        created_at_str = account.get("timestamp_created")
        current_tags = account.get("tags_resolved", []) # List of tag names
        
        # Parse Thresholds
        warmup_min = self.config.get("warmup_threshold", WARMUP_INBOX_MIN)
        
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

        found_status_tags = [t for t in current_tags if t in STATUS_TAGS]
        has_conflicts = len(found_status_tags) > 1
        
        # Determine effective current status (Prioritize based on Score if conflicting)
        status_tag = None
        if has_conflicts:
             # Specific Conflict: Sick vs Benched
             if TAG_STATUS_SICK in found_status_tags and TAG_STATUS_BENCHED in found_status_tags:
                 # Use Score as Truth (Dynamic Threshold)
                 if warmup_score < warmup_min:
                     status_tag = TAG_STATUS_SICK
                 else:
                     status_tag = TAG_STATUS_BENCHED
             else:
                # Fallback Priority
                if TAG_STATUS_SICK in found_status_tags: status_tag = TAG_STATUS_SICK
                elif TAG_STATUS_WARMING in found_status_tags: status_tag = TAG_STATUS_WARMING
                elif TAG_STATUS_BENCHED in found_status_tags: status_tag = TAG_STATUS_BENCHED
                elif TAG_STATUS_SENDING in found_status_tags: status_tag = TAG_STATUS_SENDING
        else:
            status_tag = found_status_tags[0] if found_status_tags else None

        
        logging.info(f"Evaluating {email} | Age: {age_days}d | Status: {status_tag} | Score: {warmup_score} | Conflicts: {has_conflicts}")

        # --- RULE 1: New Account Check ---
        if age_days < MIN_AGE_DAYS:
            if status_tag != TAG_STATUS_WARMING or has_conflicts:
                reason = "Rule 1: New Account (<14 days)"
                if has_conflicts and status_tag == TAG_STATUS_WARMING: reason += " (Cleanup)"
                return self._create_action(email, reason, TAG_STATUS_WARMING, warmup=True, campaigns="REMOVE")
            return None # No change needed

        # --- RULE 2: Auth Check ---
        if not auth_valid:
             if status_tag != TAG_STATUS_SICK or has_conflicts:
                reason = "Rule 2: Auth Invalid"
                if has_conflicts and status_tag == TAG_STATUS_SICK: reason += " (Cleanup)"
                return self._create_action(email, reason, TAG_STATUS_SICK, warmup=False, campaigns="REMOVE")
             return None

        # --- RULE 3: Warmup Health Check ---
        # Using Warmup Score as proxy for now since API doesn't give rates easily
        if warmup_score < warmup_min:
            if status_tag != TAG_STATUS_SICK or has_conflicts:
                 reason = f"Rule 3: Low Health Score ({warmup_score} < {warmup_min})"
                 if has_conflicts and status_tag == TAG_STATUS_SICK: reason += " (Cleanup)"
                 return self._create_action(email, reason, TAG_STATUS_SICK, warmup=True, campaigns="REMOVE")
            return None

        # --- RULE 4: Warmup Recovery Check ---
        if status_tag == TAG_STATUS_SICK:
            # Check if recovered. Requires history which we don't have easily yet.
            # Simplified: If score is perfect now, move to BENCHED
            if warmup_score > 95:
                 return self._create_action(email, "Rule 4: Recovered (Score > 95)", TAG_STATUS_BENCHED, warmup=True, campaigns="REMOVE")
            
            # If still sick, but had conflicts, clean them up
            if has_conflicts:
                return self._create_action(email, "Conflicting Status Tags (Cleanup)", TAG_STATUS_SICK, warmup=True, campaigns="REMOVE")
            return None
        
        # --- FORCED ROTATION (Takes priority over Rule 5/6 if healthy) ---
        if force_status:
             if force_status == TAG_STATUS_BENCHED and (status_tag != TAG_STATUS_BENCHED or has_conflicts):
                 return self._create_action(email, "Rule 5: Rotation Target (Force Bench)", TAG_STATUS_BENCHED, warmup=True, campaigns="REMOVE")
             
             if force_status == TAG_STATUS_SENDING and (status_tag != TAG_STATUS_SENDING or has_conflicts):
                 return self._create_action(email, "Rule 6: Rotation Target (Force Sending)", TAG_STATUS_SENDING, warmup=True, campaigns="ADD")
             
             # If force matches status but conflicts exist
             if has_conflicts and status_tag == force_status:
                  return self._create_action(email, "Conflicting Status Tags (Cleanup)", force_status, warmup=True, campaigns=None) # None campaigns preserves state

        # --- RULE 5: Bench Rotation Check (Default Logic if no force) ---
        if status_tag == TAG_STATUS_SENDING:
            if has_conflicts:
                 return self._create_action(email, "Conflicting Status Tags (Cleanup)", TAG_STATUS_SENDING, warmup=True, campaigns="ADD")
            pass

        # --- RULE 6: Return to Sending Check (Default Logic if no force) ---
        if status_tag == TAG_STATUS_BENCHED:
            # If healthy, bring back.
            if warmup_score >= 90:
                 return self._create_action(email, "Rule 6: Rested & Healthy", TAG_STATUS_SENDING, warmup=True, campaigns="ADD")
            
            if has_conflicts:
                 return self._create_action(email, "Conflicting Status Tags (Cleanup)", TAG_STATUS_BENCHED, warmup=True, campaigns="REMOVE")
            return None

        # Default: If no status tag, set to Sending if old enough
        if not status_tag and age_days >= MIN_AGE_DAYS:
             return self._create_action(email, "Rule 0: Unlabeled -> Sending", TAG_STATUS_SENDING, warmup=True, campaigns="ADD")
        
        # Catch-all conflict cleanup
        if has_conflicts and status_tag:
             return self._create_action(email, "Conflicting Status Tags (Cleanup)", status_tag, warmup=True, campaigns=None)

        return None

    def _get_status_tag(self, tags):
        for t in tags:
            if t in STATUS_TAGS:
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
