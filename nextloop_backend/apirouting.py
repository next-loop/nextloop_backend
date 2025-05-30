from ninja import NinjaAPI
from api.controllers.apiCourses import courseRouter
from api.controllers.apiRegistration import registrationrouter
from api.controllers.apiPayment import paymentrouter
from api.controllers.apiTestimonials import testimonial_router
from api.controllers.apiTeam import team_router

api = NinjaAPI()
api.add_router('/courses', courseRouter)
api.add_router('/enroll', registrationrouter)
api.add_router('/create-payment', paymentrouter)
api.add_router('/testimonials', testimonial_router)
api.add_router('/team', team_router)