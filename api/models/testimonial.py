from django.db import models
from cloudinary.models import CloudinaryField
from django.core.validators import MinValueValidator, MaxValueValidator

class Testimonial(models.Model):
    user_name = models.CharField(max_length=100)
    course_title = models.CharField(max_length=200)
    star_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    message = models.TextField()
    image = CloudinaryField('user_image', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user_name} - {self.course_title} ({self.star_rating}⭐)"



from ninja import Schema
from typing import Optional

class TestimonialOut(Schema):
    id: int
    user_name: str
    course_title: str
    star_rating: int
    message: str
    image: Optional[str]

    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=obj.id,
            user_name=obj.user_name,
            course_title=obj.course_title if hasattr(obj, 'course_title') else obj.course.title,
            star_rating=obj.star_rating,
            message=obj.message,
            image=obj.image.url if obj.image else None
        )
