"""
Course API
"""

from util.json_request import JsonResponse

from courseware.courses import (
    get_courses,
    sort_by_announcement,
    course_image_url,
    get_course_about_section,
)


def course_view(request, course_key_string):

	course_key = CourseKey.from_string(course_key_string)
	course_usage_key = modulestore().make_course_usage_key(course_key)

	return Response({
		'blocks_url': reverse(
			'blocks_in_block_tree',
			kwargs={'usage_key_string': unicode(course_usage_key)},
			request=request,
			)
		})

def list_courses (request):

	courses = get_courses (request.user)
	courses_json = []

	for course in courses:
		courses_json.append({
        "id": unicode(course.id),
        "name": course.display_name_with_default,
        "number": course.display_number_with_default,
        "organization": course.display_org_with_default,
        "description": get_course_about_section(course, "short_description").strip(),
        "startDate": course.start,
        "endDate": course.end,
        "enrollmentStartDate": course.enrollment_start,
        "enrollmentEndDate": course.enrollment_end,
        "image": course_image_url(course),
        })

   	return JsonResponse(courses_json)
