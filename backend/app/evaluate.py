"""Offline deterministic regression set. No provider calls and no accuracy claims."""
import json
from pathlib import Path
from .agent import classify_text, refund_eligible

def evaluate():
    categories = {
        "billing": ["I was charged twice", "Duplicate payment on my card", "Unrecognized charge on my statement", "Unauthorized payment", "Refund this duplicate charge"],
        "refund": ["I want a refund", "Return my headphones", "My package arrived damaged", "Refund my delayed order", "Can I return this item?"],
        "delivery": ["Where is my order?", "Package hasn't arrived", "Shipping status please", "Delivery is delayed", "Check order ORB-1042"],
        "account": ["Reset my password", "Cannot login", "Can't sign in", "My account is locked", "Password reset link missing"],
        "general": ["Hello there", "Please help me", "Do you have a physical store?", "What colors are available?", "Can I talk to someone?"],
    }
    cases = []
    for expected, texts in categories.items():
        for value in texts:
            actual = classify_text(value)
            cases.append({"kind": "classification", "input": value, "expected": expected, "actual": actual, "passed": expected == actual})
    for status in ("delayed", "processing", "damaged", "delivered"):
        for payment in ("paid", "unpaid", "refunded"):
            for days in (-1, 0, 30, 31, 45):
                expected = status != "delivered" and payment == "paid" and 0 <= days <= 30
                order = {"status": status, "payment_status": payment, "days_since_purchase": days}
                actual = refund_eligible(order)
                cases.append({"kind": "refund_boundary", "input": order, "expected": expected, "actual": actual, "passed": expected == actual})
    cases.append({"kind": "missing_order", "expected": False, "actual": refund_eligible(None), "passed": refund_eligible(None) is False})
    report = {"suite": "deterministic-demo-regressions", "total": len(cases), "passed": sum(c["passed"] for c in cases), "failed": [c for c in cases if not c["passed"]], "note": "Checks demo classification and backend refund rules; does not measure LLM or retrieval quality."}
    print(json.dumps(report, indent=2))
    output = Path("../docs/evaluation-results.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return not report["failed"]

if __name__ == "__main__":
    raise SystemExit(0 if evaluate() else 1)
