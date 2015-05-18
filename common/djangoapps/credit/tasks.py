"""
This file contains celery tasks for credit views
"""

from celery.task import task
from celery.utils.log import get_task_logger
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore
from opaque_keys import InvalidKeyError
from models import CreditCourse, CreditRequirement

LOGGER = get_task_logger(__name__)

@task()
def update_course_requirements(course_id):
    """ Updates course requirements table for course. """
    try:
        course_key = CourseKey.from_string(course_id)
        course = modulestore().get_course(course_key)
        is_credit_course = CreditCourse.is_credit_course(course_key=course_key)
        if is_credit_course:
            CreditRequirement.add_course_requirement(
                course_key=course_key,
                requirement={
                    "namespace": "grade",
                    "name": "grade",
                    "configuration": {
                        "min_grade": get_min_grade_for_credit(course)
                    }
                }
            )
    except InvalidKeyError as exc:
        LOGGER.error('Error on adding the requirements for course %s - %s', course_id, unicode(exc))
    except CreditCourse.DoesNotExist as exc:
        LOGGER.info('The course %s - %s is not a credit course', course_id, unicode(exc))
    else:
        LOGGER.debug('Requirements added for course %s', course_id)


def get_min_grade_for_credit(course):
    """ This is a dummy function to continue work.
    """
    try:
        return course.min_grade
    except:
        return 0.8
