from django.db import models
from ninja import Schema
from pydantic import BaseModel
from uuid import UUID
from typing import Optional


class view_registration_info(models.Model):
    register_id = models.IntegerField(primary_key=True)  # Assuming this is unique
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    referred_by = models.CharField(max_length=255, null=True, blank=True)
    discounted_amount = models.DecimalField(max_digits=10, decimal_places=2)
    registration_token = models.CharField(max_length=255)
    
    course_id = models.IntegerField()
    title = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False  # Important: prevents Django from trying to create or alter the view
        db_table = 'view_registration_info'  # must match the actual view name


class ViewRegistrationInfoOut(Schema):
    register_id: int
    full_name: str
    email: str
    phone_number: str
    referred_by: Optional[str]
    discounted_amount: float
    registration_token: str  # Keep it as str
    course_id: int
    title: str
    price: float

    @classmethod
    def from_orm(cls, obj):
        return cls(
            register_id=obj.register_id,
            full_name=obj.full_name,
            email=obj.email,
            phone_number=obj.phone_number,
            referred_by=obj.referred_by,
            discounted_amount=obj.discounted_amount,
            registration_token=str(obj.registration_token),  # Force cast to str
            course_id=obj.course_id,
            title=obj.title,
            price=obj.price,
        )
        
        
        

# CREATE OR REPLACE VIEW view_registration_info AS SELECT api_courseregistration.id AS register_id, api_courseregistration.full_name, api_courseregistration.email, api_courseregistration.phone_number, api_courseregistration.referred_by, api_courseregistration.discounted_amount, api_courseregistration.registration_token, api_courses.id AS course_id, api_courses.title, api_courses.price FROM api_courseregistration, api_courses WHERE api_courseregistration.course_id = api_courses.id;