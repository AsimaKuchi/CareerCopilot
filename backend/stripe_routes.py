"""
Stripe subscription routes for MyCareerCopilot.
Handles checkout, webhooks, subscription management, and usage tracking.
"""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import stripe
import os
import logging

logger = logging.getLogger("server")

stripe_router = APIRouter(tags=["stripe"])

# Initialize Stripe - loaded lazily via init
STRIPE_SECRET_KEY = None
STRIPE_PUBLISHABLE_KEY = None
STRIPE_PRO_PRICE_ID = None

# Free tier monthly limits
FREE_LIMITS = {
    "job_applications": 3,
    "resume_optimizations": 2,
    "interview_prep": 1,
    "career_paths": 1,
    "cover_letters": 2,
    "extension_uses": 3,
}

# DB reference - set by init_stripe_routes
db = None

def init_stripe_routes(database, get_current_user_func):
    """Initialize the stripe routes with database and auth dependencies."""
    global db, get_current_user, STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY, STRIPE_PRO_PRICE_ID
    db = database
    get_current_user = get_current_user_func
    STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
    STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY")
    STRIPE_PRO_PRICE_ID = os.environ.get("STRIPE_PRO_PRICE_ID")
    if STRIPE_SECRET_KEY:
        stripe.api_key = STRIPE_SECRET_KEY
        logger.info("Stripe initialized successfully")


async def get_user_plan(user_id: str) -> str:
    """Get user's current plan: 'free' or 'pro'."""
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "subscription_status": 1})
    status = (user or {}).get("subscription_status", "free")
    return "pro" if status == "active" else "free"


async def get_monthly_usage(user_id: str) -> dict:
    """Get user's usage for current month."""
    month_key = datetime.now(timezone.utc).strftime("%Y-%m")
    usage = await db.usage_tracking.find_one(
        {"user_id": user_id, "month": month_key},
        {"_id": 0}
    )
    if not usage:
        return {k: 0 for k in FREE_LIMITS}
    return {k: usage.get(k, 0) for k in FREE_LIMITS}


async def check_usage_limit(user_id: str, feature: str) -> dict:
    """
    Check if user can use a feature. Returns dict with:
    - allowed: bool
    - current: int (current usage)
    - limit: int (max allowed, -1 for unlimited)
    - plan: str
    """
    plan = await get_user_plan(user_id)
    if plan == "pro":
        return {"allowed": True, "current": 0, "limit": -1, "plan": "pro"}

    if feature not in FREE_LIMITS:
        return {"allowed": True, "current": 0, "limit": -1, "plan": plan}

    usage = await get_monthly_usage(user_id)
    current = usage.get(feature, 0)
    limit = FREE_LIMITS[feature]

    return {
        "allowed": current < limit,
        "current": current,
        "limit": limit,
        "plan": plan,
    }


async def increment_usage(user_id: str, feature: str):
    """Increment usage counter for a feature."""
    month_key = datetime.now(timezone.utc).strftime("%Y-%m")
    await db.usage_tracking.update_one(
        {"user_id": user_id, "month": month_key},
        {
            "$inc": {feature: 1},
            "$set": {"updated_at": datetime.now(timezone.utc)},
            "$setOnInsert": {"created_at": datetime.now(timezone.utc)},
        },
        upsert=True,
    )


# ========================
# STRIPE ENDPOINTS
# ========================

@stripe_router.get("/stripe/config")
async def get_stripe_config():
    """Return Stripe publishable key for frontend."""
    return {"publishable_key": STRIPE_PUBLISHABLE_KEY}


@stripe_router.post("/stripe/create-checkout")
async def create_checkout_session(request: Request):
    """Create a Stripe Checkout Session for Pro subscription."""
    user = await get_current_user(request)
    body = await request.json()
    origin_url = body.get("origin_url", "")

    if not origin_url:
        raise HTTPException(400, "origin_url is required")

    if not STRIPE_SECRET_KEY or not STRIPE_PRO_PRICE_ID:
        raise HTTPException(500, "Stripe not configured")

    # Check if user already has active subscription
    user_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
    if user_doc and user_doc.get("subscription_status") == "active":
        raise HTTPException(400, "You already have an active Pro subscription")

    # Get or create Stripe customer
    stripe_customer_id = (user_doc or {}).get("stripe_customer_id")
    if not stripe_customer_id:
        customer = stripe.Customer.create(
            email=user.email,
            name=user.name,
            metadata={"user_id": user.user_id},
        )
        stripe_customer_id = customer.id
        await db.users.update_one(
            {"user_id": user.user_id},
            {"$set": {"stripe_customer_id": stripe_customer_id}},
        )

    success_url = f"{origin_url}/billing?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{origin_url}/pricing"

    session = stripe.checkout.Session.create(
        customer=stripe_customer_id,
        mode="subscription",
        line_items=[{"price": STRIPE_PRO_PRICE_ID, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"user_id": user.user_id},
    )

    # Create payment transaction record
    await db.payment_transactions.insert_one({
        "user_id": user.user_id,
        "email": user.email,
        "session_id": session.id,
        "stripe_customer_id": stripe_customer_id,
        "amount": 19.99,
        "currency": "usd",
        "payment_status": "initiated",
        "metadata": {"user_id": user.user_id, "plan": "pro_monthly"},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    })

    return {"url": session.url, "session_id": session.id}


@stripe_router.get("/stripe/checkout-status/{session_id}")
async def get_checkout_status(session_id: str, request: Request):
    """Check the status of a checkout session and update subscription."""
    user = await get_current_user(request)

    session = stripe.checkout.Session.retrieve(session_id)

    # Update payment transaction
    new_status = "paid" if session.payment_status == "paid" else session.payment_status
    await db.payment_transactions.update_one(
        {"session_id": session_id},
        {"$set": {
            "payment_status": new_status,
            "status": session.status,
            "updated_at": datetime.now(timezone.utc),
        }},
    )

    # If paid, activate subscription (idempotent - check if already processed)
    if session.payment_status == "paid" and session.status == "complete":
        existing = await db.payment_transactions.find_one(
            {"session_id": session_id, "processed": True}
        )
        if not existing:
            subscription_id = session.subscription
            await db.users.update_one(
                {"user_id": user.user_id},
                {"$set": {
                    "subscription_status": "active",
                    "stripe_subscription_id": subscription_id,
                    "plan": "pro",
                    "subscription_started_at": datetime.now(timezone.utc),
                }},
            )
            await db.payment_transactions.update_one(
                {"session_id": session_id},
                {"$set": {"processed": True}},
            )
            logger.info(f"Subscription activated for user {user.user_id}")

    return {
        "status": session.status,
        "payment_status": session.payment_status,
        "amount_total": session.amount_total,
        "currency": session.currency,
    }


@stripe_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        # For test mode, we may not have webhook secret, so parse directly
        event = stripe.Event.construct_from(
            stripe.util.convert_to_stripe_object(
                __import__("json").loads(payload),
                stripe.api_key,
            ),
            stripe.api_key,
        )
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(400, f"Webhook error: {str(e)}")

    event_type = event.type
    data = event.data.object

    logger.info(f"Stripe webhook: {event_type}")

    if event_type == "customer.subscription.created":
        customer_id = data.customer
        user = await db.users.find_one({"stripe_customer_id": customer_id}, {"_id": 0})
        if user:
            await db.users.update_one(
                {"user_id": user["user_id"]},
                {"$set": {
                    "subscription_status": "active",
                    "stripe_subscription_id": data.id,
                    "plan": "pro",
                    "subscription_started_at": datetime.now(timezone.utc),
                }},
            )

    elif event_type == "customer.subscription.updated":
        customer_id = data.customer
        status = data.status  # active, past_due, canceled, unpaid
        user = await db.users.find_one({"stripe_customer_id": customer_id}, {"_id": 0})
        if user:
            plan = "pro" if status == "active" else "free"
            await db.users.update_one(
                {"user_id": user["user_id"]},
                {"$set": {
                    "subscription_status": status,
                    "plan": plan,
                }},
            )

    elif event_type == "customer.subscription.deleted":
        customer_id = data.customer
        user = await db.users.find_one({"stripe_customer_id": customer_id}, {"_id": 0})
        if user:
            await db.users.update_one(
                {"user_id": user["user_id"]},
                {"$set": {
                    "subscription_status": "cancelled",
                    "plan": "free",
                    "subscription_ended_at": datetime.now(timezone.utc),
                }},
            )

    elif event_type == "invoice.payment_failed":
        customer_id = data.customer
        user = await db.users.find_one({"stripe_customer_id": customer_id}, {"_id": 0})
        if user:
            await db.users.update_one(
                {"user_id": user["user_id"]},
                {"$set": {"subscription_status": "past_due"}},
            )

    return {"status": "ok"}


# ========================
# SUBSCRIPTION MANAGEMENT
# ========================

@stripe_router.get("/subscription")
async def get_subscription(request: Request):
    """Get user's subscription status and usage."""
    user = await get_current_user(request)
    user_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})

    plan = "pro" if (user_doc or {}).get("subscription_status") == "active" else "free"
    usage = await get_monthly_usage(user.user_id)

    # Build limits with usage
    limits = {}
    for feature, limit in FREE_LIMITS.items():
        current = usage.get(feature, 0)
        limits[feature] = {
            "current": current,
            "limit": limit if plan == "free" else -1,
            "remaining": max(0, limit - current) if plan == "free" else -1,
        }

    result = {
        "plan": plan,
        "subscription_status": (user_doc or {}).get("subscription_status", "free"),
        "usage": limits,
        "stripe_customer_id": (user_doc or {}).get("stripe_customer_id"),
        "subscription_started_at": None,
    }

    started = (user_doc or {}).get("subscription_started_at")
    if started:
        result["subscription_started_at"] = started.isoformat() if hasattr(started, "isoformat") else str(started)

    # Get next billing date from Stripe if active
    sub_id = (user_doc or {}).get("stripe_subscription_id")
    if plan == "pro" and sub_id:
        try:
            sub = stripe.Subscription.retrieve(sub_id)
            result["current_period_end"] = datetime.fromtimestamp(sub.current_period_end, tz=timezone.utc).isoformat()
            result["cancel_at_period_end"] = sub.cancel_at_period_end
        except Exception as e:
            logger.error(f"Error fetching subscription: {e}")

    return result


@stripe_router.post("/subscription/cancel")
async def cancel_subscription(request: Request):
    """Cancel subscription at end of billing period."""
    user = await get_current_user(request)
    user_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})

    sub_id = (user_doc or {}).get("stripe_subscription_id")
    if not sub_id:
        raise HTTPException(400, "No active subscription found")

    try:
        # Cancel at end of period (user keeps access until then)
        stripe.Subscription.modify(sub_id, cancel_at_period_end=True)
        await db.users.update_one(
            {"user_id": user.user_id},
            {"$set": {"subscription_status": "cancelling"}},
        )
        return {"message": "Subscription will be cancelled at the end of your billing period"}
    except stripe.error.StripeError as e:
        raise HTTPException(400, str(e))


@stripe_router.post("/subscription/reactivate")
async def reactivate_subscription(request: Request):
    """Reactivate a subscription that was set to cancel."""
    user = await get_current_user(request)
    user_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})

    sub_id = (user_doc or {}).get("stripe_subscription_id")
    if not sub_id:
        raise HTTPException(400, "No subscription found")

    try:
        stripe.Subscription.modify(sub_id, cancel_at_period_end=False)
        await db.users.update_one(
            {"user_id": user.user_id},
            {"$set": {"subscription_status": "active", "plan": "pro"}},
        )
        return {"message": "Subscription reactivated"}
    except stripe.error.StripeError as e:
        raise HTTPException(400, str(e))


@stripe_router.get("/subscription/invoices")
async def get_invoices(request: Request):
    """Get user's payment history."""
    user = await get_current_user(request)
    user_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})

    customer_id = (user_doc or {}).get("stripe_customer_id")
    if not customer_id:
        return {"invoices": []}

    try:
        invoices = stripe.Invoice.list(customer=customer_id, limit=12)
        return {
            "invoices": [
                {
                    "id": inv.id,
                    "amount": inv.amount_paid / 100,
                    "currency": inv.currency,
                    "status": inv.status,
                    "created": datetime.fromtimestamp(inv.created, tz=timezone.utc).isoformat(),
                    "invoice_url": inv.hosted_invoice_url,
                    "pdf_url": inv.invoice_pdf,
                }
                for inv in invoices.data
            ]
        }
    except stripe.error.StripeError as e:
        logger.error(f"Error fetching invoices: {e}")
        return {"invoices": []}


@stripe_router.post("/subscription/update-payment")
async def update_payment_method(request: Request):
    """Create a Stripe billing portal session for updating payment method."""
    user = await get_current_user(request)
    body = await request.json()
    origin_url = body.get("origin_url", "")

    user_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
    customer_id = (user_doc or {}).get("stripe_customer_id")

    if not customer_id:
        raise HTTPException(400, "No billing account found")

    try:
        portal_session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=f"{origin_url}/billing",
        )
        return {"url": portal_session.url}
    except stripe.error.StripeError as e:
        raise HTTPException(400, str(e))
