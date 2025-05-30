from django.db import models
from cloudinary.models import CloudinaryField

class TeamMember(models.Model):
    name = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    description = models.TextField()
    photo = CloudinaryField('photo', blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.designation}"


from ninja import Schema
from typing import Optional

class TeamMemberOut(Schema):
    id: int
    name: str
    designation: str
    description: str
    photo: Optional[str]  # URL for the image
