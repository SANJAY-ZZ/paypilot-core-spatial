import random
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from backend.app.core.database import SessionLocal, init_db
from backend.app.models.merchant import Merchant
from backend.app.models.customer import Customer
from backend.app.models.product import Product
from backend.app.models.order import Order
from backend.app.models.payment import Payment
from backend.app.models.opportunity import Opportunity
from backend.app.models.guardian_policy import GuardianPolicy
from backend.app.models.audit_event import AuditEvent
from backend.app.models.ai_action import AIAction
from backend.app.services.opportunity_engine import opportunity_engine


def seed_database(db: Session) -> None:
    """Populates database with deterministic seed data for Kora Retail."""
    # Reset random seed for absolute reproducibility
    random.seed(42)

    # Check if already seeded
    existing = db.query(Merchant).filter(Merchant.id == "mer_koraretail").first()
    if existing:
        return

    print("[SEED] Seeding PayPilot database with Kora Retail dataset...")

    # 1. Create Merchant
    merchant = Merchant(
        id="mer_koraretail",
        name="Kora Retail",
        currency="INR",
        total_revenue=842300.0,
        created_at=datetime.now(timezone.utc) - timedelta(days=180),
    )
    db.add(merchant)
    db.flush()

    # 2. Create Guardian Policy
    policy = GuardianPolicy(
        id="pol_koraretail_default",
        merchant_id=merchant.id,
        max_discount_percent=15.0,
        max_campaign_budget=10000.0,
        max_customer_count=500,
        min_ai_confidence=0.75,
        require_approval_above_amount=5000.0,
        created_at=datetime.now(timezone.utc) - timedelta(days=180),
    )
    db.add(policy)

    # 3. Create Products (30 items across Apparel, Footwear, Accessories, Home)
    product_catalogs = [
        ("Silk Jacquard Kurta", "Apparel", 2850.0, 45),
        ("Classic Linen Shirt - Olive", "Apparel", 1950.0, 60),
        ("Slim Fit Raw Indigo Denim", "Apparel", 2499.0, 35),
        ("Handloom Cotton Kurti", "Apparel", 1450.0, 80),
        ("Tailored Chino Trousers", "Apparel", 2199.0, 50),
        ("Bohemian Floral Midi Dress", "Apparel", 2750.0, 30),
        ("Unstructured Summer Blazer", "Apparel", 4200.0, 20),
        ("Supima Cotton Crew Tee", "Apparel", 899.0, 150),
        ("Knitted Pique Polo Shirt", "Apparel", 1299.0, 95),
        ("Relaxed French Terry Hoodie", "Apparel", 2250.0, 40),
        ("Handcrafted Leather Loafers", "Footwear", 3499.0, 25),
        ("Urban Minimalist Sneakers", "Footwear", 2999.0, 55),
        ("Artisan Kolhapuri Chappals", "Footwear", 1250.0, 70),
        ("Oxford Formal Brogues", "Footwear", 3999.0, 18),
        ("Canvas Slip-On Shoes", "Footwear", 1499.0, 65),
        ("Tan Suede Chelsea Boots", "Footwear", 4499.0, 15),
        ("Full Grain Leather Belt", "Accessories", 1150.0, 85),
        ("Bifold RFID Leather Wallet", "Accessories", 1450.0, 90),
        ("Polarized Aviator Sunglasses", "Accessories", 1850.0, 40),
        ("Vintage Brass Cufflinks", "Accessories", 850.0, 110),
        ("Pure Silk Printed Pocket Square", "Accessories", 650.0, 120),
        ("Waxed Canvas Daily Backpack", "Accessories", 3250.0, 28),
        ("Hand-Stitched Leather Watch Strap", "Accessories", 750.0, 75),
        ("Hand-Tufted Wool Cushion Cover", "Home", 950.0, 60),
        ("Soy Wax Amber & Clove Candle", "Home", 750.0, 140),
        ("Studio Ceramic Coffee Mug Set", "Home", 1250.0, 50),
        ("Handcrafted Brass Diya Lantern", "Home", 1650.0, 40),
        ("Waffle Weave Cotton Throw", "Home", 1850.0, 35),
        ("Braided Jute Planter Pot", "Home", 650.0, 90),
        ("Hammered Ayurvedic Copper Bottle", "Home", 1150.0, 80),
    ]

    products = []
    for idx, (name, cat, price, inv) in enumerate(product_catalogs):
        prod = Product(
            id=f"prod_kora_{idx + 1:03d}",
            merchant_id=merchant.id,
            name=name,
            category=cat,
            price=price,
            inventory=inv,
            created_at=datetime.now(timezone.utc) - timedelta(days=170),
        )
        products.append(prod)
        db.add(prod)
    db.flush()

    # 4. Create 1,024 Customers
    first_names = [
        "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan", "Krishna", "Ishaan",
        "Shaurya", "Atharv", "Advik", "Pranav", "Kabir", "Rohan", "Ananya", "Diya", "Saanvi", "Aadhya",
        "Pari", "Anika", "Navya", "Angel", "Myra", "Avani", "Isha", "Riya", "Tanvi", "Tara",
        "Kavya", "Sneha", "Pooja", "Meera", "Vikram", "Siddharth", "Rahul", "Sameer", "Gaurav", "Amit",
        "Priya", "Neha", "Shreya", "Kriti", "Karan", "Manish", "Deepak", "Nikhil", "Akash", "Varun"
    ]
    last_names = [
        "Sharma", "Verma", "Patel", "Mehta", "Reddy", "Nair", "Iyer", "Rao", "Gupta", "Singh",
        "Kaur", "Deshmukh", "Joshi", "Bose", "Banerjee", "Chatterjee", "Menon", "Pillai", "Choudhury", "Das",
        "Malhotra", "Kapoor", "Khanna", "Bhatia", "Bhatt", "Saxena", "Mishra", "Pandey", "Dubey", "Tiwari"
    ]

    customers = []
    now = datetime.now(timezone.utc)

    # 23 specific failed payment amounts summing up to exactly ₹38,400.0
    failed_recovery_amounts = [
        1850.0, 1200.0, 2400.0, 950.0, 1650.0, 3100.0, 1450.0, 850.0, 2200.0, 1750.0,
        1900.0, 1150.0, 2600.0, 1350.0, 990.0, 2100.0, 1550.0, 1800.0, 1250.0, 2050.0,
        1400.0, 1600.0, 1260.0,
    ]  # Sum = 38,400.0

    for i in range(1024):
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        cust_id = f"cust_kora_{i + 1:04d}"
        email = f"{fn.lower()}.{ln.lower()}{i + 1}@example.com"

        if i < 23:
            # 23 Recovery customers
            churn_risk = round(random.uniform(0.30, 0.60), 2)
            repeat_prob = round(random.uniform(0.60, 0.85), 2)
            upsell_prob = round(random.uniform(0.50, 0.75), 2)
            order_count = random.randint(1, 4)
            aov = failed_recovery_amounts[i]
            ltv = aov * order_count
            last_purchase = now - timedelta(hours=random.randint(4, 68))
        elif i < 150:
            # Dormant high-LTV customers for win-back
            churn_risk = round(random.uniform(0.65, 0.95), 2)
            repeat_prob = round(random.uniform(0.40, 0.65), 2)
            upsell_prob = round(random.uniform(0.30, 0.55), 2)
            order_count = random.randint(3, 8)
            aov = round(random.uniform(1800, 3500), 2)
            ltv = round(aov * order_count, 2)
            last_purchase = now - timedelta(days=random.randint(48, 120))
        elif i < 400:
            # High-affinity repeat customers for upsell
            churn_risk = round(random.uniform(0.05, 0.25), 2)
            repeat_prob = round(random.uniform(0.75, 0.96), 2)
            upsell_prob = round(random.uniform(0.70, 0.92), 2)
            order_count = random.randint(3, 12)
            aov = round(random.uniform(1500, 4200), 2)
            ltv = round(aov * order_count, 2)
            last_purchase = now - timedelta(days=random.randint(2, 25))
        else:
            # Standard customers
            churn_risk = round(random.uniform(0.20, 0.55), 2)
            repeat_prob = round(random.uniform(0.35, 0.70), 2)
            upsell_prob = round(random.uniform(0.30, 0.65), 2)
            order_count = random.randint(1, 5)
            aov = round(random.uniform(900, 2800), 2)
            ltv = round(aov * order_count, 2)
            last_purchase = now - timedelta(days=random.randint(5, 90))

        cust = Customer(
            id=cust_id,
            merchant_id=merchant.id,
            name=f"{fn} {ln}",
            email=email,
            lifetime_value=ltv,
            order_count=order_count,
            average_order_value=aov,
            last_purchase_at=last_purchase,
            churn_risk=churn_risk,
            repeat_probability=repeat_prob,
            upsell_probability=upsell_prob,
            created_at=now - timedelta(days=random.randint(90, 180)),
        )
        customers.append(cust)
        db.add(cust)
    db.flush()

    # 5. Create Payments & Orders (Total = 4,892 transactions)
    # Total revenue target: ₹8,42,300 across ~4,845 successful payments (avg ~₹173.85 per item or aggregate basket)
    # Plus 23 failed recovery payments (₹38,400), 12 mandate failures, 12 pending, 15 refunded

    orders_to_create = []
    payments_to_create = []
    tx_count = 0

    # A. Create the 23 Recent Failed Recovery Payments (Sum = 38,400.0)
    for i in range(23):
        cust = customers[i]
        amount = failed_recovery_amounts[i]
        created_time = now - timedelta(hours=random.randint(6, 68))

        ord_obj = Order(
            id=f"ord_kora_fail_{i + 1:03d}",
            merchant_id=merchant.id,
            customer_id=cust.id,
            total_amount=amount,
            status="failed",
            created_at=created_time,
        )
        orders_to_create.append(ord_obj)

        pmt_obj = Payment(
            id=f"pay_kora_fail_{i + 1:03d}",
            merchant_id=merchant.id,
            customer_id=cust.id,
            order_id=ord_obj.id,
            amount=amount,
            status="failed",
            failure_reason=random.choice([
                "payment_authentication_failed",
                "insufficient_funds",
                "bank_server_timeout",
                "upi_pin_validation_timeout",
            ]),
            razorpay_reference=f"pay_mock_rzp_fail_{i + 1:03d}",
            created_at=created_time,
        )
        payments_to_create.append(pmt_obj)
        tx_count += 1

    # B. Create 12 Recurring Mandate Failures
    for i in range(12):
        cust = customers[23 + i]
        amount = 1299.0
        created_time = now - timedelta(days=random.randint(1, 14))

        ord_obj = Order(
            id=f"ord_kora_subfail_{i + 1:03d}",
            merchant_id=merchant.id,
            customer_id=cust.id,
            total_amount=amount,
            status="failed",
            created_at=created_time,
        )
        orders_to_create.append(ord_obj)

        pmt_obj = Payment(
            id=f"pay_kora_subfail_{i + 1:03d}",
            merchant_id=merchant.id,
            customer_id=cust.id,
            order_id=ord_obj.id,
            amount=amount,
            status="failed",
            failure_reason="mandate_auto_debit_failed",
            razorpay_reference=f"pay_mock_rzp_subfail_{i + 1:03d}",
            created_at=created_time,
        )
        payments_to_create.append(pmt_obj)
        tx_count += 1

    # C. Create 12 Pending and 15 Refunded
    for i in range(12):
        cust = customers[40 + i]
        amount = round(random.uniform(900, 2200), 2)
        created_time = now - timedelta(days=random.randint(1, 30))

        ord_obj = Order(
            id=f"ord_kora_pnd_{i + 1:03d}",
            merchant_id=merchant.id,
            customer_id=cust.id,
            total_amount=amount,
            status="pending",
            created_at=created_time,
        )
        orders_to_create.append(ord_obj)

        pmt_obj = Payment(
            id=f"pay_kora_pnd_{i + 1:03d}",
            merchant_id=merchant.id,
            customer_id=cust.id,
            order_id=ord_obj.id,
            amount=amount,
            status="pending",
            failure_reason=None,
            razorpay_reference=f"pay_mock_rzp_pnd_{i + 1:03d}",
            created_at=created_time,
        )
        payments_to_create.append(pmt_obj)
        tx_count += 1

    for i in range(15):
        cust = customers[60 + i]
        amount = round(random.uniform(1200, 2500), 2)
        created_time = now - timedelta(days=random.randint(10, 60))

        ord_obj = Order(
            id=f"ord_kora_ref_{i + 1:03d}",
            merchant_id=merchant.id,
            customer_id=cust.id,
            total_amount=amount,
            status="refunded",
            created_at=created_time,
        )
        orders_to_create.append(ord_obj)

        pmt_obj = Payment(
            id=f"pay_kora_ref_{i + 1:03d}",
            merchant_id=merchant.id,
            customer_id=cust.id,
            order_id=ord_obj.id,
            amount=amount,
            status="refunded",
            failure_reason="customer_cancellation",
            razorpay_reference=f"pay_mock_rzp_ref_{i + 1:03d}",
            created_at=created_time,
        )
        payments_to_create.append(pmt_obj)
        tx_count += 1

    # D. Generate remaining successful transactions to hit 4,892 total and ₹8,42,300 total revenue
    remaining_transactions = 4892 - tx_count  # 4830 successful payments
    target_successful_revenue = 842300.0

    # Create synthetic price points that sum up precisely to target_successful_revenue
    raw_weights = [random.uniform(0.5, 3.0) for _ in range(remaining_transactions)]
    total_w = sum(raw_weights)
    allocated_amounts = [round((w / total_w) * target_successful_revenue, 2) for w in raw_weights]
    diff = target_successful_revenue - sum(allocated_amounts)
    allocated_amounts[0] = round(allocated_amounts[0] + diff, 2)

    for i in range(remaining_transactions):
        cust = customers[23 + (i % (len(customers) - 23))]
        amount = allocated_amounts[i]
        days_ago = random.randint(1, 160)
        created_time = now - timedelta(days=days_ago, minutes=random.randint(0, 1440))

        ord_obj = Order(
            id=f"ord_kora_succ_{i + 1:05d}",
            merchant_id=merchant.id,
            customer_id=cust.id,
            total_amount=amount,
            status="completed",
            created_at=created_time,
        )
        orders_to_create.append(ord_obj)

        pmt_obj = Payment(
            id=f"pay_kora_succ_{i + 1:05d}",
            merchant_id=merchant.id,
            customer_id=cust.id,
            order_id=ord_obj.id,
            amount=amount,
            status="success",
            failure_reason=None,
            razorpay_reference=f"pay_mock_rzp_succ_{i + 1:05d}",
            created_at=created_time,
        )
        payments_to_create.append(pmt_obj)

    # Bulk insert orders & payments in batches
    db.bulk_save_objects(orders_to_create)
    db.bulk_save_objects(payments_to_create)
    db.commit()

    # 6. Run Opportunity Discovery Engine & Generate AI Opportunities (Target: ~27 opportunities)
    # First, run core engine detection
    opportunity_engine.scan_all_opportunities(db, merchant.id)

    # Create additional specialized sub-cohort opportunities to reach target count of 27
    specialized_opportunities = [
        # Payment Recovery sub-segments
        ("payment_recovery", "UPI Intent Drops on High-Value Orders", 18200.0, 0.95, "low", 8, "8 customers experienced UPI intent app switches with incomplete authorization.", "payment_recovery_link"),
        ("payment_recovery", "Card 3DS Authentication Timeouts", 12400.0, 0.93, "low", 9, "9 customers dropped off during bank OTP verification screen.", "payment_recovery_link"),
        ("payment_recovery", "NetBanking Gateway Latency Fallbacks", 7800.0, 0.91, "low", 6, "6 customers experienced inter-bank gateway connection timeouts.", "payment_recovery_link"),

        # Customer Win-Back sub-segments
        ("customer_winback", "Q3 Festive Shoppers Re-Engagement", 45000.0, 0.85, "medium", 64, "64 high-AOV Diwali season buyers have reached their historical re-order cadence.", "winback_discount_campaign"),
        ("customer_winback", "Luxury Apparel Buyers 60-Day Re-Activation", 38500.0, 0.82, "medium", 28, "28 premium collection customers haven't browsed new catalog arrivals in 60 days.", "winback_discount_campaign"),
        ("customer_winback", "Footwear Enthusiasts Win-Back Nudge", 26400.0, 0.80, "medium", 42, "42 verified footwear purchasers showed recent dormant browsing behavior.", "winback_discount_campaign"),
        ("customer_winback", "Lapsed Weekend Flash Sale Shoppers", 19200.0, 0.78, "medium", 35, "35 price-sensitive buyers inactive for >45 days.", "winback_discount_campaign"),
        ("customer_winback", "High LTV VIP Tier Re-Connection", 52000.0, 0.88, "low", 15, "15 top 5% revenue contributors inactive for 40 days.", "winback_discount_campaign"),

        # Upsell sub-segments
        ("upsell", "Linen Apparel & Leather Accessory Pairings", 34200.0, 0.89, "low", 55, "55 linen shirt buyers have not yet browsed coordinating full-grain leather belts.", "smart_upsell_nudge"),
        ("upsell", "Formal Brogue Footwear Cross-Sell to Suit Buyers", 41000.0, 0.87, "low", 38, "38 blazer purchasers have high affinity for Oxford brogues.", "smart_upsell_nudge"),
        ("upsell", "Festive Home Decor Bundle Recommendations", 22800.0, 0.86, "low", 46, "46 home catalog buyers frequently add brass lamps with cushion sets.", "smart_upsell_nudge"),
        ("upsell", "Premium Silk Scarf Add-On at Checkout", 15400.0, 0.84, "low", 72, "72 dress purchasers show high attachment probability for silk accessories.", "smart_upsell_nudge"),
        ("upsell", "Ayurvedic Copper Bottle Post-Purchase Upgrade", 11200.0, 0.88, "low", 48, "48 health & lifestyle product buyers eligible for instant 1-click add-on.", "smart_upsell_nudge"),
        ("upsell", "Handcrafted Kolhapuri Chappals Cross-Sell", 18900.0, 0.83, "low", 60, "60 ethnic wear buyers have shown repeated interest in traditional footwear.", "smart_upsell_nudge"),
        ("upsell", "Weekend Travel Duffel & Backpack Upgrade", 29500.0, 0.85, "low", 32, "32 accessories customers with high cart value potential.", "smart_upsell_nudge"),
        ("upsell", "Cotton Lounge Wear Bundle Nudge", 16800.0, 0.87, "low", 58, "58 casual wear buyers eligible for 3-pack bundle saving incentive.", "smart_upsell_nudge"),

        # Subscription & Recurring
        ("subscription_recovery", "Monthly Wardrobe Refresh Mandate Sync", 15588.0, 0.91, "low", 12, "12 recurring monthly subscription auto-debit mandates failed due to card expiry.", "recurring_mandate_refresh"),
        ("subscription_recovery", "VIP Club Membership Auto-Renewal", 8990.0, 0.93, "low", 10, "10 VIP club subscribers have impending renewal mandate failure.", "recurring_mandate_refresh"),
        ("subscription_recovery", "Curated Home Aroma Refill Drop-Off", 6200.0, 0.89, "low", 8, "8 recurring candle & fragrance subscribers with failed UPI mandate.", "recurring_mandate_refresh"),

        # Additional specific tactical opportunities
        ("customer_winback", "Cart Abandoners on High Margin SKUs", 28000.0, 0.84, "medium", 32, "32 customers abandoned checkout with blazers and footwear in cart.", "winback_discount_campaign"),
        ("upsell", "Monsoon Footwear Protection Add-On", 9400.0, 0.86, "low", 40, "40 leather shoe buyers eligible for waterproof wax kit cross-sell.", "smart_upsell_nudge"),
        ("customer_winback", "Festive Coupon Non-Redeemers", 21500.0, 0.79, "medium", 44, "44 customers received promo vouchers but did not complete transaction.", "winback_discount_campaign"),
        ("upsell", "Smart Watch Strap Multi-Pack Upsell", 12000.0, 0.88, "low", 50, "50 watch strap buyers with multi-color compatibility interest.", "smart_upsell_nudge"),
    ]

    base_opp_count = db.query(Opportunity).count()
    for sp_idx, (opp_type, title, pot_rev, conf, risk, cust_cnt, reason, rec_act) in enumerate(specialized_opportunities):
        opp_rec = Opportunity(
            id=f"opp_kora_sp_{base_opp_count + sp_idx + 1:03d}",
            merchant_id=merchant.id,
            type=opp_type,
            title=title,
            potential_revenue=pot_rev,
            confidence=conf,
            risk=risk,
            affected_customer_count=cust_cnt,
            reason=reason,
            recommended_action=rec_act,
            status="discovered",
            created_at=now - timedelta(hours=random.randint(1, 48)),
        )
        db.add(opp_rec)

    db.commit()

    # 7. Seed Initial Sample AI Actions and Audit Events
    opps = db.query(Opportunity).filter(Opportunity.merchant_id == merchant.id).all()
    if opps:
        # Create a sample proposed action
        action1 = AIAction(
            id="act_kora_sample_001",
            merchant_id=merchant.id,
            opportunity_id=opps[0].id,
            agent="strategist",
            action_type="payment_recovery_link",
            payload={
                "action_name": "payment_recovery_link",
                "discount_percent": 0.0,
                "campaign_budget": 500.0,
                "customer_count": 23,
                "estimated_revenue": 38400.0,
                "estimated_cost": 500.0,
                "channel": "Razorpay Smart Links + Automated WhatsApp/Email",
            },
            confidence=0.94,
            status="approved",
            guardian_result={
                "decision": "approved",
                "reason": "Action strictly complies with all merchant-configured financial guardrails and risk thresholds.",
                "risk_level": "low",
                "policy_checks": [
                    {"rule_name": "max_discount_percent", "passed": True, "threshold": 15.0, "actual_value": 0.0, "message": "Discount within allowable limit."},
                    {"rule_name": "max_campaign_budget", "passed": True, "threshold": 10000.0, "actual_value": 500.0, "message": "Campaign budget within allowable limit."},
                    {"rule_name": "max_customer_count", "passed": True, "threshold": 500, "actual_value": 23, "message": "Target customer cohort within safe limit."},
                    {"rule_name": "min_ai_confidence", "passed": True, "threshold": 0.75, "actual_value": 0.94, "message": "AI confidence satisfies safety bar."},
                    {"rule_name": "require_approval_above_amount", "passed": True, "threshold": 5000.0, "actual_value": 500.0, "message": "Within autonomous financial execution threshold."},
                ],
            },
            execution_result=None,
            created_at=now - timedelta(hours=2),
        )
        db.add(action1)

        # Audit events for action1
        db.add(
            AuditEvent(
                id="aud_kora_001",
                merchant_id=merchant.id,
                action_id=action1.id,
                agent="scout",
                event_type="OPPORTUNITY_DISCOVERED",
                reason="Scout agent discovered 23 failed payment records representing ₹38,400.",
                metadata_json={"potential_revenue": 38400.0, "affected_customers": 23},
                status="recorded",
                created_at=now - timedelta(hours=3),
            )
        )
        db.add(
            AuditEvent(
                id="aud_kora_002",
                merchant_id=merchant.id,
                action_id=action1.id,
                agent="strategist",
                event_type="ACTION_PROPOSED",
                reason="Strategist agent packaged payment recovery link campaign.",
                metadata_json={"action_id": action1.id, "channel": "Razorpay Smart Links"},
                status="recorded",
                created_at=now - timedelta(hours=2, minutes=30),
            )
        )
        db.add(
            AuditEvent(
                id="aud_kora_003",
                merchant_id=merchant.id,
                action_id=action1.id,
                agent="guardian",
                event_type="GUARDIAN_APPROVED",
                reason="Guardian policy checks passed with 100% compliance.",
                metadata_json={"decision": "approved", "risk_level": "low"},
                status="recorded",
                created_at=now - timedelta(hours=2),
            )
        )

    db.commit()

    total_opps = db.query(Opportunity).filter(Opportunity.merchant_id == merchant.id).count()
    total_cust = db.query(Customer).filter(Customer.merchant_id == merchant.id).count()
    total_tx = db.query(Payment).filter(Payment.merchant_id == merchant.id).count()
    print(f"[SUCCESS] Seeding complete: Merchant '{merchant.name}' | Customers: {total_cust} | Transactions: {total_tx} | Opportunities: {total_opps}")


if __name__ == "__main__":
    init_db()
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
