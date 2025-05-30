from ninja import Router

from api.models.testimonial import Testimonial, TestimonialOut

testimonial_router = Router(tags=["Testimonial APIs"])

@testimonial_router.get("/", response=list[TestimonialOut])
def get_testimonials(request):
    testimonials = Testimonial.objects.order_by("-created_at")[:4]
    return [TestimonialOut.from_orm(t) for t in testimonials]
