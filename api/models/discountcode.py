from django.db import models

class DiscountCode(models.Model):
    code = models.CharField(max_length=100, unique=True, null=False)
    discount_percent = models.FloatField(null=False)

    def __str__(self):
        return f"Discount Code: {self.code} -- Discount: {self.discount_percent}%"
