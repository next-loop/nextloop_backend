from ninja import Router

from django.shortcuts import get_object_or_404
from django.db import DatabaseError
from requests import Response
from api.models.courses import Courses
from api.models.registration import CourseRegistration, CourseRegistrationIn, CourseRegistrationOut, UpdateCouponCode
from api.models.discountcode import DiscountCode
from api.models.view_registration_info import ViewRegistrationInfoOut, view_registration_info

registrationrouter = Router(tags=["Registration APIs"])


import random
import string
from django.utils.text import slugify

def generate_unique_referral_code(full_name):
    base = slugify(full_name).replace('-', '')[:6]  # max 6 chars from name
    while True:
        suffix = ''.join(random.choices(string.digits, k=4))  # 4-digit suffix
        code = f"{base}{suffix}".upper()
        if not CourseRegistration.objects.filter(referral_code=code).exists():
            return code



@registrationrouter.post("/register", response=CourseRegistrationOut)
def register_course(request, data: CourseRegistrationIn):
    try:
        course = get_object_or_404(Courses, id=data.course)
        original_price = course.price
        referred_code = None

        if data.referred_by:
            # Validate referral code exists in CourseRegistration (previously generated codes)
            if CourseRegistration.objects.filter(referral_code=data.referred_by).exists():
                referred_code = data.referred_by
            else:
                return Response(
                    {"error": "Invalid referral code. Please check and try again."},
                    status=HTTP_400_BAD_REQUEST
                )

        # Generate referral code for the new registrant
        new_referral_code = generate_unique_referral_code(data.full_name)

        registration = CourseRegistration.objects.create(
            full_name=data.full_name,
            email=data.email,
            phone_number=data.phone_number,
            referred_by=referred_code,
            referral_code=new_referral_code,
            course=course,
            original_amount=original_price,
            discounted_amount=original_price,  # No discount applied here
        )

        return CourseRegistrationOut.from_orm(registration)

    except Courses.DoesNotExist:
        return Response({"error": "Course not found."}, status=HTTP_404_NOT_FOUND)

    except Exception as e:
        # ✅ Print error in the console
        print("Error during course registration:", str(e))
        return Response(
            {"error": "An unexpected error occurred.", "details": str(e)},
            status=HTTP_500_INTERNAL_SERVER_ERROR
        )


# api/controllers/apiRegistration.py

from ninja import Router
from ninja.responses import Response
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR
)
from django.shortcuts import get_object_or_404
from django.db import DatabaseError

@registrationrouter.put("/apply-coupon", summary="Apply coupon to registration")
def apply_coupon_code(request, data: UpdateCouponCode):
    try:
        registration = get_object_or_404(CourseRegistration, id=data.registrationid)

        if registration.is_paid:
            return Response(
                {"error": "Coupon cannot be applied. Registration is already marked as paid."},
                status=HTTP_400_BAD_REQUEST,
            )

        if registration.course.id != data.courseid:
            return Response(
                {"error": "The provided course ID does not match the registration record."},
                status=HTTP_400_BAD_REQUEST
            )

        try:
            discount_code = DiscountCode.objects.get(code=data.code)
        except DiscountCode.DoesNotExist:
            return Response(
                {"error": "Invalid discount coupon."},
                status=HTTP_404_NOT_FOUND
            )

        discount = discount_code.discount_percent
        original_price = registration.original_amount
        discounted_price = round(original_price * (1 - discount / 100), 2)

        # Apply the discount now
        registration.discounted_amount = discounted_price
        registration.discount_coupon = data.code
        registration.save()

        return {
            "message": "Coupon applied successfully!",
            "original_price": original_price,
            "discount_percent": discount,
            "discounted_price": discounted_price,
            "registration_id": registration.id,
        }

    except DatabaseError as db_err:
        return Response(
            {"error": "A database error occurred. Please try again later."},
            status=HTTP_500_INTERNAL_SERVER_ERROR
        )

    except Exception as e:
        return Response(
            {"error": "An unexpected error occurred. Please contact support if the issue persists."},
            status=HTTP_500_INTERNAL_SERVER_ERROR
        )


@registrationrouter.get("/{token}", response=ViewRegistrationInfoOut)
def list_registrations_view(request, token: str):
    try:
        data = view_registration_info.objects.get(registration_token=token)
        return ViewRegistrationInfoOut.from_orm(data)  # <-- Return schema instance to handle conversions
    except view_registration_info.DoesNotExist:
        return Response({"error": f"No registration found with token '{token}'"}, status=404)
    except Exception as e:
        return Response({"error": "Failed to fetch registration info", "details": str(e)}, status=500)

    
    
    

