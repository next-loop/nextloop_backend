from typing import Optional
from django.db import models
from ninja import Schema
from cloudinary.models import CloudinaryField

class Courses(models.Model):
    title = models.TextField()
    level_tag = models.TextField()
    description = models.TextField()
    duration = models.TextField()
    purchase_count = models.IntegerField()
    price = models.FloatField() 
    image = CloudinaryField('image', blank=True, null=True)

    def __str__(self):
        return f"Title : {self.title} -- Price : {self.price}"
    
    
    
class CoursesIn(Schema):
    title : str
    level_tag : str
    description : str
    duration : str
    purchase_count : int
    price : float
    
    
class CoursesOut(Schema):
    id: int
    title: str
    level_tag: str
    description: str
    duration: str
    purchase_count: int
    price: float
    image: Optional[str]

    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=obj.id,
            title=obj.title,
            level_tag=obj.level_tag,
            description=obj.description,
            duration=obj.duration,
            purchase_count=obj.purchase_count,
            price=obj.price,
            image=obj.image.url if obj.image else None,
        )

    
    
class CourseSchema(Schema):
    id: int
    title: str