from ninja import Router
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.conf import settings
import requests
import json
import uuid
from datetime import datetime

from api.models.payment import payment, paymentIn
from api.models.courses import Courses
from api.models.registration import CourseRegistration

from django.core.mail import send_mail
from django.conf import settings


paymentrouter = Router(tags=["Payment APIs"])

# Cashfree configuration
CASHFREE_BASE_URL = "https://api.cashfree.com"
CASHFREE_APP_ID = "77107481798f19dd72ae4279d1470177"
CASHFREE_SECRET_KEY = "cfsk_ma_prod_c9c7c59366cd2247c9b04c54fb530be2_1b0e1aa0"


@paymentrouter.post("/create-payment")
def create_payment(request, data: paymentIn):
    try:
        # Validate course and registration
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
                    "message": "Pending payment already exists for this registration",
                    "transaction_id": str(existing_payment.transaction_id),
                    "amount": existing_payment.payable_amount,
                    "status": "Pending",
                    "payment_link": existing_payment.cashfree_payment_session_id
                }, status=200)

        # Create payment without order_id (to avoid unique constraint violation)
        payment_entry = payment.objects.create(
            course=course,
            courseregistration=registration,
            customerid=registration.id,
            payable_amount=registration.discounted_amount,
            payment_status=False,
            order_id=None
        )

        # Generate unique order_id from transaction_id
        order_id = f"ORDER_{payment_entry.transaction_id}"

        print(f"[DEBUG] Transaction ID: {payment_entry.transaction_id}")
        print(f"[DEBUG] Generated Order ID: {order_id}")

        # Prepare Cashfree customer details
        customer_details = {
            "customer_id": str(registration.id),
            "customer_email": registration.email,
            "customer_phone": registration.phone_number,
        }

        # Create order via Cashfree
        cashfree_response = create_cashfree_order(
            order_id=order_id,
            amount=payment_entry.payable_amount,
            customer_details=customer_details
        )

        if not cashfree_response.get("success"):
            payment_entry.delete()
            print(f"[ERROR] Cashfree Order Failed: {cashfree_response}")
            return JsonResponse({"error": "Failed to create payment order", "details": cashfree_response}, status=500)

        # Update payment with order details
        payment_entry.order_id = order_id
        payment_entry.cashfree_payment_session_id = cashfree_response["data"].get("payment_session_id")
        payment_entry.save()

        print(f"[INFO] Payment session created successfully for transaction {payment_entry.transaction_id}")

        return JsonResponse({
            "message": "Payment initialized",
            "transaction_id": str(payment_entry.transaction_id),
            "amount": payment_entry.payable_amount,
            "status": "Pending",
            "payment_link": cashfree_response["data"].get("payment_link"),
            "payment_session_id": cashfree_response["data"].get("payment_session_id")
        }, status=201)

    except Exception as e:
        print(f"[EXCEPTION] create_payment error: {str(e)}")
        return JsonResponse({"error": "An unexpected error occurred", "details": str(e)}, status=500)


def create_cashfree_order(order_id, amount, customer_details):
    """Helper to create Cashfree order"""
    url = f"{CASHFREE_BASE_URL}/pg/orders"

    headers = {
        "Content-Type": "application/json",
        "x-client-id": CASHFREE_APP_ID,
        "x-client-secret": CASHFREE_SECRET_KEY,
        "x-api-version": "2022-09-01"
    }

    payload = {
        "order_id": order_id,
        "order_amount": amount,
        "order_currency": "INR",
        "order_note": "Course registration payment",
        "customer_details": customer_details,
        "order_meta": {
            "return_url": f"{settings.FRONTEND_URL}/payment/callback?order_id={order_id}"
        }
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response_data = response.json()

        print(f"[DEBUG] Cashfree API response: {response_data}")

        if response.status_code == 200:
            return {
                "success": True,
                "data": {
                    "payment_session_id": response_data.get("payment_session_id"),
                    "payment_link": response_data.get("payment_link")
                }
            }
        else:
            return {
                "success": False,
                "error": response_data.get("message", "Unknown error"),
                "status_code": response.status_code
            }

    except Exception as e:
        print(f"[EXCEPTION] create_cashfree_order error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


from django.http import HttpResponse
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404
import json

@paymentrouter.post("/payment-webhook")
def cashfree_webhook(request):
    print("Webhook Called")
    try:
        payload = json.loads(request.body)
        print("Webhook Payload:", payload)

        data = payload.get("data", {})
        order = data.get("order", {})
        payment_data = data.get("payment", {})

        order_id = order.get("order_id")
        payment_status = payment_data.get("payment_status")
        failure_reason = payment_data.get("error_message", "Payment failed or status not SUCCESS")

        print(f"Order ID: {order_id}, Payment Status: {payment_status}")

        transaction_uuid = order_id.replace("ORDER_", "")
        payment_entry = get_object_or_404(payment, transaction_id=transaction_uuid)

        # Always store the order ID
        payment_entry.order_id = order_id

        if payment_status == "SUCCESS":
            payment_entry.payment_status = True
            payment_entry.failure_reason = None
            payment_entry.save()
            print("Payment marked as successful in DB")

            registration = payment_entry.courseregistration
            registration.is_paid = True
            registration.save()
            print("Course registration marked as paid")

            # HTML email template with referral code
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

            # Send HTML email
            send_mail(
                subject="Payment Confirmation - Thank you for registering!",
                message="Thank you for your payment. Please view this email in an HTML-capable email client.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[registration.email],
                fail_silently=False,
                html_message=html_message
            )
            print("Confirmation HTML email sent to user.")

        else:
            payment_entry.payment_status = False
            payment_entry.failure_reason = failure_reason
            payment_entry.save()
            print(f"Payment failed or pending: {failure_reason}")

        return HttpResponse(status=200)

    except Exception as e:
        print("Error occurred during webhook processing:", str(e))
        return HttpResponse(status=500)
    
    

from ninja import Router
from ninja.responses import Response
from typing import Optional
from pydantic import BaseModel


# ✅ Define the response schema
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

# ✅ GET /verify/{order_id}
@paymentrouter.get("/verify/{order_id}", response=PaymentVerifyResponseSchema)
def verify_payment(request, order_id: str):
    try:
        payment_details = payment.objects.select_related("course", "courseregistration").get(
            cashfree_payment_session_id=order_id
        )

        return {
            "status": "Completed" if payment_details.payment_status else "Failed",
            "message": "Payment data retrieved successfully",
            "amount": payment_details.payable_amount,
            "transaction_id": str(payment_details.transaction_id),
            "error_message": payment_details.failure_reason if not payment_details.payment_status else None,
            "course_title": payment_details.course.title if payment_details.course else None,
            "customer_name": payment_details.courseregistration.full_name if payment_details.courseregistration else None,
            "customer_email": payment_details.courseregistration.email if payment_details.courseregistration else None,
            "customer_phone": payment_details.courseregistration.phone_number if payment_details.courseregistration else None,
        }


    except payment.DoesNotExist:
        return Response(
            {
                "status": "Failed",
                "message": "Payment verification failed",
                "error_message": "Invalid order ID"
            },
            status=404
        )

    except Exception as e:
        return Response(
            {
                "status": "Failed",
                "message": "An error occurred during payment verification",
                "error_message": str(e)
            },
            status=500
        )
