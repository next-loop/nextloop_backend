from django.contrib import admin
from api.models.courses import Courses
from api.models.discountcode import DiscountCode
from api.models.registration import CourseRegistration
from api.models.payment import payment

# Register your models here.

admin.site.register(CourseRegistration)
admin.site.register(DiscountCode)
admin.site.register(payment)



@admin.register(Courses)
class CoursesAdmin(admin.ModelAdmin):
    list_display = ("title", "price", "purchase_count")
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" style="max-height: 200px;" />'
        return "No image uploaded"
    image_preview.allow_tags = True
    image_preview.short_description = "Image Preview"