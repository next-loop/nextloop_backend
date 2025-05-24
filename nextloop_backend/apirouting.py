from ninja import NinjaAPI
from api.controllers.apiCourses import courseRouter
from api.controllers.apiRegistration import registrationrouter
from api.controllers.apiPayment import paymentrouter

api = NinjaAPI()
api.add_router('/courses', courseRouter)
api.add_router('/enroll', registrationrouter)
api.add_router('/create-payment', paymentrouter)