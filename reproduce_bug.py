
from inboxbench.execution.decision_engine import DecisionEngine
import logging
import sys

# Setup logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

# Mock Account State
mock_account = {
    "email": "michael@sipesautomation.com",
    "timestamp_created": "2024-01-01T00:00:00Z", # Old enough
    "tags_resolved": ["Sick", "Benched", "Active"], # Conflict!
    "stat_warmup_score": 95
}

# Mock Config (User Threshold 98)
mock_config = {
    "warmup_threshold": 98
}

class MockAPI:
    def get_tag_id_by_name(self, name): return "tag_" + name 

print("--- Testing Decision Engine ---")
print(f"Account: {mock_account}")
print(f"Config: {mock_config}")

engine = DecisionEngine(MockAPI(), config=mock_config)
action = engine.evaluate_account(mock_account)

print("\n--- Result ---")
if action:
    print(f"ACTION: {action['new_tag']} | Reason: {action['reason']}")
else:
    print("NO ACTION (None)")
