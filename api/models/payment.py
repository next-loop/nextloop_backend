from django.db import models
import uuid
from ninja import Schema
from api.models.courses import Courses
from api.models.registration import CourseRegistration


class payment(models.Model):
    course = models.ForeignKey(Courses, on_delete=models.CASCADE)
    courseregistration = models.ForeignKey(CourseRegistration, on_delete=models.CASCADE)
    transaction_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    customerid = models.BigIntegerField()
    payable_amount = models.FloatField()
    registration_at = models.DateTimeField(auto_now_add=True)
    payment_status = models.BooleanField(default=False)
    failure_reason = models.TextField(null=True, blank=True)
    
    # Updated fields with longer lengths
    order_id = models.CharField(max_length=255, unique=True, null=True)
    cashfree_order_id = models.CharField(max_length=256, null=True, blank=True)
    cashfree_payment_session_id = models.CharField(max_length=512, null=True, blank=True)
    payment_method = models.CharField(max_length=100, null=True, blank=True)
    payment_completion_time = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Course : {self.course.title} -- {self.courseregistration.full_name} -- Amount : {self.payable_amount} -- Status : {self.payment_status}"
    
class paymentIn(Schema):
    course : int
    courseregistration : int




