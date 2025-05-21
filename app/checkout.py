# app/checkout.py
import os
import stripe
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.config import settings  # تأكد إنك تحمل STRIPE_SECRET_KEY

stripe.api_key = settings.stripe_secret_key

router = APIRouter()

@router.post("/create-checkout-session")
async def create_checkout_session():
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "unit_amount": 1000,       # السعر بالمئة؛ هنا 10.00$
                    "product_data": {
                        "name": "Waste Classifier Model",
                        "description": "License to use the AI Waste Classifier",
                        # "images": ["https://…/model.png"],
                    },
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=f"{settings.domain}/Checkoutsuccess",
            cancel_url=f"{settings.domain}/", 
        )
        return JSONResponse({"sessionId": session.id})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
