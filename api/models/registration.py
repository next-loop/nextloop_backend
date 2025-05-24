from django.db import models
from ninja import Schema
from api.models.courses import Courses,  CourseSchema
from typing import Optional
from datetime import datetime
import uuid
from uuid import UUID

class CourseRegistration(models.Model):
    course = models.ForeignKey('Courses', on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    referred_by = models.CharField(max_length=100, blank=True, null=True)
    discount_coupon = models.CharField(max_length=100, blank=True, null=True)
    referral_code = models.CharField(max_length=100, unique=True, blank=True, null=True)  # NEW FIELD
    registered_at = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)
    registration_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    original_amount = models.FloatField()
    discounted_amount = models.FloatField()
    created_at = models.DateField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} - {self.course.title}"

    
    
from ninja import Schema
from typing import Optional
from datetime import datetime
from uuid import UUID
from api.models.courses import CourseSchema

class CourseRegistrationIn(Schema):
    full_name: str
    email: str
    phone_number: str
    referred_by: Optional[str] = None
    course: int  # Course ID


class CourseRegistrationOut(Schema):
    id: int
    full_name: str
    email: str
    phone_number: str
    referred_by: Optional[str]
    referral_code: Optional[str]  # <-- NEW
    course: CourseSchema
    registered_at: Optional[datetime]
    registration_token: str
    original_amount: float
    discounted_amount: float

    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=obj.id,
            full_name=obj.full_name,
            email=obj.email,
            phone_number=obj.phone_number,
            referred_by=obj.referred_by,
            referral_code=obj.referral_code,
            course=CourseSchema.from_orm(obj.course),
            registered_at=obj.registered_at,
            registration_token=str(obj.registration_token),
            original_amount=obj.original_amount,
            discounted_amount=obj.discounted_amount,
        )


class UpdateCouponCode(Schema):
    registrationid: int
    courseid: int
    code: str

    