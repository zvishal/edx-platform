"""
This file contains receivers of course publication signals.
"""

import logging

from django.dispatch import receiver
from django.utils import timezone
from opaque_keys.edx.keys import CourseKey

from xmodule.modulestore.django import SignalHandler
from openedx.core.djangoapps.credit.partition_schemes import VerificationPartitionScheme
from openedx.core.djangoapps.signals.signals import GRADES_UPDATED
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.exceptions import ItemNotFoundError

log = logging.getLogger(__name__)

# XBlocks that can be added as credit requirements
CREDIT_REQUIREMENT_XBLOCK_CATEGORIES = "edx-reverification-block"

def on_course_publish(course_key):  # pylint: disable=unused-argument
    """
    Will receive a delegated 'course_published' signal from cms/djangoapps/contentstore/signals.py
    and kick off a celery task to update the credit course requirements.

    IMPORTANT: It is assumed that the edx-proctoring subsystem has been appropriate refreshed
    with any on_publish event workflow *BEFORE* this method is called.
    """

    # Import here, because signal is registered at startup, but items in tasks
    # are not yet able to be loaded
    from openedx.core.djangoapps.credit import api, tasks
    tag_contents_with_partitions(course_key)

    if api.is_credit_course(course_key):
        tasks.update_credit_course_requirements.delay(unicode(course_key))
        log.info(u'Added task to update credit requirements for course "%s" to the task queue', course_key)


@receiver(GRADES_UPDATED)
def listen_for_grade_calculation(sender, username, grade_summary, course_key, deadline, **kwargs):  # pylint: disable=unused-argument
    """Receive 'MIN_GRADE_REQUIREMENT_STATUS' signal and update minimum grade
    requirement status.

    Args:
        sender: None
        username(string): user name
        grade_summary(dict): Dict containing output from the course grader
        course_key(CourseKey): The key for the course
        deadline(datetime): Course end date or None

    Kwargs:
        kwargs : None

    """
    # This needs to be imported here to avoid a circular dependency
    # that can cause syncdb to fail.
    from openedx.core.djangoapps.credit import api

    course_id = CourseKey.from_string(unicode(course_key))
    is_credit = api.is_credit_course(course_id)
    if is_credit:
        requirements = api.get_credit_requirements(course_id, namespace='grade')
        if requirements:
            criteria = requirements[0].get('criteria')
            if criteria:
                min_grade = criteria.get('min_grade')
                if grade_summary['percent'] >= min_grade:
                    reason_dict = {'final_grade': grade_summary['percent']}
                    api.set_credit_requirement_status(
                        username, course_id, 'grade', 'grade', status="satisfied", reason=reason_dict
                    )
                elif deadline and deadline < timezone.now():
                    api.set_credit_requirement_status(
                        username, course_id, 'grade', 'grade', status="failed", reason={}
                    )


def tag_contents_with_partitions(course_key):
    # just an example code
    # persist the value as a course tag
    # course_tag_api.set_course_tag(user, course_key, partition_key, group.id)

    credit_reqs_xblocks = _get_credit_requirements_xblocks(course_key)
    for xblock in credit_reqs_xblocks:
        partition = VerificationPartitionScheme()
        xblock.group_access = {
            partition.key_for_partition(xblock.get_credit_requirement_name()): [
                partition.VERIFIED_ALLOW, partition.VERIFIED_DENY
            ]
        }
        xblock.save()

    pass


def _get_credit_requirements_xblocks(course_key):
    """
    Retrieve all XBlocks in the course for a particular category.

    Returns only XBlocks that are published and haven't been deleted.
    """
    xblocks = [
        block for block in modulestore().get_items(
            course_key,
            qualifiers={"category": CREDIT_REQUIREMENT_XBLOCK_CATEGORIES},
            revision=ModuleStoreEnum.RevisionOption.published_only,
        )
        if _is_in_course_tree(block)
    ]
    return xblocks


def _is_in_course_tree(block):
    """
    Check that the XBlock is in the course tree.

    It's possible that the XBlock is not in the course tree
    if its parent has been deleted and is now an orphan.
    """
    ancestor = block.get_parent()
    while ancestor is not None and ancestor.location.category != "course":
        ancestor = ancestor.get_parent()

    return ancestor is not None
