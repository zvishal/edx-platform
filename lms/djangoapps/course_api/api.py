"""
Course API
"""

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.response import Response

from courseware.courses import (
    get_courses,
    sort_by_announcement,
    course_image_url,
    get_course_about_section,
)


def has_permission(request, username):

    if not username:
        return False

    user = request.user
    return user and (user.is_staff or user.username == username)


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


def list_courses(request, username):

    if (has_permission(request, username) != True):
        return Response('Unathorized', status=status.HTTP_403_FORBIDDEN)

    if (username != ''):
        new_user = User.objects.get(username=username)
    else:
        new_user = request.user

    courses = get_courses(new_user)
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

    return Response(courses_json)
