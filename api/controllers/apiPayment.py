from ninja import Router
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.core.mail import send_mail
from api.models.payment import payment, paymentIn
from api.models.courses import Courses
from api.models.registration import CourseRegistration
import razorpay
import json
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from ninja.responses import Response

# # Razorpay Configuration
# RAZORPAY_KEY_ID = "rzp_test_QQd4iMqsM9ccBI"
# RAZORPAY_KEY_SECRET = "WWKYxnbJvn4Y30aIvOGB4hGD"
# razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))


# Razorpay Configuration
RAZORPAY_KEY_ID = "rzp_live_rly0BJKgu8Z5zG"
RAZORPAY_KEY_SECRET = "bAlyCxqVb9V9Exi3B3THCvrF"
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

paymentrouter = Router(tags=["Payment APIs"])

@paymentrouter.post("/create-payment")
def create_payment(request, data: paymentIn):
    try:
        course = get_object_or_404(Courses, id=data.course)
        registration = get_object_or_404(CourseRegistration, id=data.courseregistration)

        if registration.course.id != course.id:
            return JsonResponse({"error": "Registration does not belong to the given course"}, status=400)

        existing_payment = payment.objects.filter(courseregistration=registration).first()
        if existing_payment:
            if existing_payment.payment_status:
                return JsonResponse({
                    "error": "Payment already completed for this registration",
                    "transaction_id": str(existing_payment.transaction_id),
                    "amount": existing_payment.payable_amount,
                    "status": "Completed"
                }, status=400)
            else:
                return JsonResponse({
                    "message": "Pending payment already exists",
                    "transaction_id": str(existing_payment.transaction_id),
                    "amount": existing_payment.payable_amount,
                    "status": "Pending",
                    "payment_link": None
                }, status=200)

        # Create new payment entry
        payment_entry = payment.objects.create(
            course=course,
            courseregistration=registration,
            customerid=registration.id,
            payable_amount=registration.discounted_amount,
            payment_status=False,
            order_id=None
        )

        # Shorten the order_id to max 40 characters
        short_receipt = f"ORD-{str(payment_entry.transaction_id)[:36]}"

        customer_details = {
            "customer_email": registration.email,
            "customer_phone": registration.phone_number
        }

        razorpay_response = create_razorpay_order(short_receipt, payment_entry.payable_amount, customer_details)

        if not razorpay_response.get("success"):
            payment_entry.delete()
            return JsonResponse({"error": "Failed to create Razorpay order", "details": razorpay_response}, status=500)

        payment_entry.order_id = razorpay_response["data"].get("order_id")
        payment_entry.cashfree_payment_session_id = razorpay_response["data"].get("order_id")
        payment_entry.save()

        return JsonResponse({
            "message": "Payment initialized",
            "transaction_id": str(payment_entry.transaction_id),
            "amount": payment_entry.payable_amount,
            "status": "Pending",
            "razorpay_order_id": razorpay_response["data"].get("order_id")
        }, status=201)

    except Exception as e:
        return JsonResponse({"error": "Unexpected error", "details": str(e)}, status=500)


def create_razorpay_order(receipt, amount, customer_details):
    try:
        razorpay_order = razorpay_client.order.create({
            "amount": int(amount * 100),  # Convert to paise
            "currency": "INR",
            "receipt": receipt,
            "payment_capture": 1,
            "notes": customer_details
        })
        return {
            "success": True,
            "data": {
                "order_id": razorpay_order["id"],
                "amount": razorpay_order["amount"],
                "currency": razorpay_order["currency"]
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

import logging

logger = logging.getLogger(__name__)

@paymentrouter.post("/payment-webhook")
def razorpay_webhook(request):
    try:
        payload = json.loads(request.body)
        event = payload.get("event")
        payment_data = payload.get("payload", {}).get("payment", {}).get("entity", {})

        razorpay_order_id = payment_data.get("order_id")
        status = payment_data.get("status")

        payment_entry = get_object_or_404(payment, order_id=razorpay_order_id)

        if status == "captured":
            payment_entry.payment_status = True
            payment_entry.failure_reason = None
            payment_entry.save()

            registration = payment_entry.courseregistration
            registration.is_paid = True
            registration.save()

            html_message = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    .container {{
                        background-color: #f9f9f9;
                        padding: 20px;
                        border-radius: 5px;
                    }}
                    .header {{
                        background-color: #4CAF50;
                        color: white;
                        padding: 10px;
                        text-align: center;
                        border-radius: 5px 5px 0 0;
                    }}
                    .content {{
                        padding: 20px;
                        background-color: white;
                    }}
                    .details {{
                        margin: 20px 0;
                        padding: 10px;
                        background-color: #f0f0f0;
                        border-radius: 5px;
                    }}
                    .footer {{
                        text-align: center;
                        margin-top: 20px;
                        color: #666;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>Payment Confirmation</h2>
                    </div>
                    <div class="content">
                        <p>Dear {registration.full_name},</p>
                        <p>Thank you for your payment for the course "<strong>{payment_entry.course.title}</strong>". 
                        We're excited to have you on board!</p>
                        
                        <div class="details">
                            <h3>Payment Details</h3>
                            <p><strong>Transaction ID:</strong> {payment_entry.transaction_id}</p>
                            <p><strong>Amount Paid:</strong> ₹{payment_entry.payable_amount}</p>
                            <p><strong>Course:</strong> {payment_entry.course.title}</p>
                            <p><strong>Registration Date:</strong> {registration.created_at.strftime('%d %B %Y')}</p>
                            <p><strong>Email:</strong> {registration.email}</p>
                            <p><strong>Your Referrer Code:</strong> {registration.referral_code if registration.referral_code else 'Not provided'}</p>
                        </div>
                        
                        <p>You'll receive further details about the course soon. If you have any questions, 
                        please contact our support team.</p>
                    </div>
                    <div class="footer">
                        <p>Best regards,<br>Your Team</p>
                    </div>
                </div>
            </body>
            </html>
            """
            send_mail(
                "Payment Confirmation",
                "Your payment is confirmed.",
                settings.DEFAULT_FROM_EMAIL,
                [registration.email],
                html_message=html_message,
                fail_silently=False
            )
        else:
            payment_entry.payment_status = False
            payment_entry.failure_reason = payment_data.get("error_description", "Failed")
            payment_entry.save()

        return HttpResponse(status=200)

    except Exception as e:
        logger.error(f"Webhook Error: {str(e)}", exc_info=True)
        return JsonResponse({"error": "Webhook failed", "details": str(e)}, status=500)


class PaymentVerifyResponseSchema(BaseModel):
    status: str
    message: Optional[str] = None
    amount: Optional[float] = None
    transaction_id: Optional[str] = None
    error_message: Optional[str] = None
    course_title: Optional[str] = None
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None


import razorpay

@paymentrouter.get("/verify/{order_id}")
def verify_payment(request, order_id):
    client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

    # Get all payments for this order
    payments = client.order.payments(order_id)
    successful_payment = None
    for p in payments['items']:
        if p['status'] == 'captured':
            successful_payment = p
            break

    if successful_payment:
        return JsonResponse({
            "status": "Success",
            "message": "Payment verified",
            "payment_id": successful_payment["id"],
            "amount": successful_payment["amount"] / 100
        })
    else:
        return JsonResponse({
            "status": "Failed",
            "message": "Payment not captured yet"
        })
