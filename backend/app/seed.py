from sqlalchemy import select
from .models import SessionLocal, Organization, User, Ticket, Message, Order, Document, Audit
from .auth import hash_password

DEMO_PASSWORD = "DemoPass123!"

def seed_demo():
    with SessionLocal() as db:
        if db.scalar(select(Organization).where(Organization.id == "org-orbit")):
            return
        db.add_all([Organization(id="org-orbit", name="Orbit Commerce"), Organization(id="org-north", name="Northstar Labs")])
        db.flush()
        password = hash_password(DEMO_PASSWORD)
        db.add_all([
            User(id="user-owner", org_id="org-orbit", name="Alex Morgan", email="owner@orbit.demo", role="owner", password_hash=password),
            User(id="user-agent", org_id="org-orbit", name="Sam Rivera", email="agent@orbit.demo", role="agent", password_hash=password),
            User(id="user-customer", org_id="org-orbit", name="Priya Sharma", email="priya@orbit.demo", role="customer", password_hash=password),
            User(id="user-customer2", org_id="org-orbit", name="Jordan Lee", email="jordan@orbit.demo", role="customer", password_hash=password),
            User(id="user-north", org_id="org-north", name="Taylor Chen", email="owner@northstar.demo", role="owner", password_hash=password),
        ])
        db.flush()
        db.add_all([
            Document(id="doc-refund", org_id="org-orbit", title="Returns & refund policy", body="Customers may request a refund within 30 days of purchase for a paid order that has not been delivered or has arrived damaged. Refunds require workspace owner approval. Refund only the original amount and currency. Never refund an unpaid or already refunded order. Cite this policy when recommending a refund."),
            Document(id="doc-shipping", org_id="org-orbit", title="Shipping & delivery guide", body="Standard shipping takes 3–5 business days. For delayed or undelivered orders, verify the order and payment status. If the paid order is undelivered within 30 days of purchase, offer an owner-approved refund or escalate to a human. Do not claim delivery dates not present in the order record."),
            Document(id="doc-account", org_id="org-orbit", title="Account & billing help", body="For login problems, direct customers to the password-reset link on the sign-in page. Support must never ask for passwords or payment card details. For duplicate payments or unrecognized charges, escalate to a human billing specialist. Do not refund a charge without a verified order and owner approval."),
            Document(id="doc-north", org_id="org-north", title="Private Northstar policy", body="Northstar internal policy. This document must never be visible to another organization."),
        ])
        db.add_all([
            Order(id="order-1", org_id="org-orbit", customer_id="user-customer", reference="ORB-1042", product="Studio Wireless Headphones", amount_cents=799900, status="delayed", days_since_purchase=8),
            Order(id="order-2", org_id="org-orbit", customer_id="user-customer2", reference="ORB-1043", product="Everyday Carry Backpack", amount_cents=349900, status="delivered", days_since_purchase=4),
            Order(id="order-3", org_id="org-orbit", customer_id="user-customer", reference="ORB-1044", product="Desk Essentials Kit", amount_cents=249900, status="processing", days_since_purchase=1),
            Order(id="order-4", org_id="org-orbit", customer_id="user-customer", reference="ORB-1001", product="Mechanical Keyboard", amount_cents=599900, status="delayed", days_since_purchase=45),
        ])
        samples = [
            ("ticket-1", "RD-1042", "user-customer", "Payment went through, but my order never arrived", "Hi! I ordered the Studio Wireless Headphones eight days ago. The payment was deducted but my order still hasn't arrived. Can I get a refund? Order ORB-1042.", "delivery", "high", "open", "ORB-1042"),
            ("ticket-2", "RD-1043", "user-customer2", "How do I reset my account password?", "I can't sign in to my account. Could you help me reset my password?", "account", "normal", "open", ""),
            ("ticket-3", "RD-1044", "user-customer", "Checking on my Desk Essentials Kit", "Could you check the shipping status of order ORB-1044? Thank you!", "delivery", "normal", "open", "ORB-1044"),
            ("ticket-4", "RD-1045", "user-customer2", "I think I've been charged twice", "There are two charges on my statement for the same purchase. Please investigate.", "billing", "urgent", "open", "ORB-1043"),
            ("ticket-5", "RD-1046", "user-customer", "Refund for an older keyboard order", "I want a refund for my delayed keyboard order ORB-1001. I purchased it 45 days ago.", "refund", "normal", "open", "ORB-1001"),
        ]
        for id_, number, customer, subject, body, category, priority, status, order in samples:
            db.add(Ticket(id=id_, number=number, org_id="org-orbit", customer_id=customer, subject=subject, description=body, category=category, priority=priority, status=status, order_reference=order))
            db.flush()
            db.add(Message(ticket_id=id_, author="Priya Sharma" if customer == "user-customer" else "Jordan Lee", kind="customer", body=body))
        db.add(Ticket(id="ticket-private", number="RD-9001", org_id="org-north", customer_id="user-north", subject="Private Northstar request", description="A separate tenant's private ticket.", order_reference=""))
        db.add(Audit(org_id="org-orbit", actor="System", action="demo.seeded", resource="Orbit Commerce"))
        db.commit()
