from asgiref.sync import sync_to_async
from django.http import Http404
from ninja import Router
from typing import List
from api.models.courses import Courses, CoursesIn, CoursesOut
from ninja.errors import HttpError

courseRouter = Router(tags=["Courses APIs"])


from typing import List

@courseRouter.get("/", response=List[CoursesOut])
def list_courses(request):
    try:
        courses = Courses.objects.all()
        return [CoursesOut.from_orm(course) for course in courses]
    except Exception as e:
        raise HttpError(500, f"Internal Server Error: {str(e)}")

@courseRouter.get("/{course_id}", response=CoursesOut)
def get_course(request, course_id: str):
    try:
        course = Courses.objects.get(id=course_id)
        return CoursesOut.from_orm(course)  # use your custom method here
    except Courses.DoesNotExist:
        raise HttpError(404, f"Course with ID {course_id} not found.")
    except Exception as e:
        raise HttpError(500, f"Internal Server Error: {str(e)}")



# @courseRouter.post("/", response=CoursesOut)
# def create_course(request, data: CoursesIn):
#     try:
#         course = Courses.objects.create(**data.dict())
#         return course
#     except Exception as e:
#         raise HttpError(500, f"Error creating course: {str(e)}")


# @courseRouter.put("/{course_id}", response=CoursesOut)
# def update_course(request, course_id: int, data: CoursesIn):
#     try:
#         course = Courses.objects.get(id=course_id)
#         for attr, value in data.dict().items():
#             setattr(course, attr, value)
#         course.save()
#         return course
#     except Courses.DoesNotExist:
#         raise HttpError(404, f"Course with ID {course_id} not found.")
#     except Exception as e:
#         raise HttpError(500, f"Error updating course: {str(e)}")


# @courseRouter.delete("/{course_id}")
# def delete_course(request, course_id: int):
#     try:
#         course = Courses.objects.get(id=course_id)
#         course.delete()
#         return {"success": True, "message": f"Course ID {course_id} deleted successfully."}
#     except Courses.DoesNotExist:
#         raise HttpError(404, f"Course with ID {course_id} not found.")
#     except Exception as e:
#         raise HttpError(500, f"Error deleting course: {str(e)}")
