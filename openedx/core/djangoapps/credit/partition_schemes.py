"""
Provides partition support to the user service.
"""

import logging

from course_modes.models import CourseMode
from lms.djangoapps.verify_student.models import SkippedReverification, VerificationStatus
from student.models import CourseEnrollment


log = logging.getLogger(__name__)


class VerificationPartitionScheme(object):
    """
    This scheme randomly assigns users into the partition's groups.
    """
    NON_VERIFIED = 'non_verified'
    VERIFIED_ALLOW = 'verified_allow'
    VERIFIED_DENY = 'verified_deny'

    @classmethod
    def get_group_for_user(cls, course_key, user, user_partition):
        """
        Return the user's group depending their enrollment and verification
        status.

        Args:
            user(User): user object
            course_id(CourseKey): CourseKey

        Returns:
            Boolean
        """
        checkpoint = user_partition.parameters["location"]

        if (
                not is_enrolled_in_verified_mode(user, course_key) or
                was_denied_at_any_checkpoint(user, course_key)
        ):
            return cls.NON_VERIFIED
        elif (
                has_skipped_any_checkpoint(user, course_key) or
                has_completed_checkpoint(user, course_key, checkpoint)
        ):
            return cls.VERIFIED_ALLOW
        else:
            return cls.VERIFIED_DENY

    @classmethod
    def key_for_partition(cls, xblock_location_id):
        """ Returns the key for partition scheme to use for look up and save
        the user's group for a given 'VerificationPartitionScheme'.

        Args:
            xblock_location_id(str): Location of block in course

        Returns:
            String of the format 'verification:{location}'
        """
        return 'verification:{0}'.format(xblock_location_id)


def is_enrolled_in_verified_mode(user, course_key):
    """
    Returns the Boolean value if given user for the given course is enrolled in
    verified modes.

    Args:
        user(User): user object
        course_id(CourseKey): CourseKey

    Returns:
        Boolean
    """
    enrollment_mode, __ = CourseEnrollment.enrollment_mode_for_user(user, course_key)
    return enrollment_mode in CourseMode.VERIFIED_MODES


def was_denied_at_any_checkpoint(user, course_key):
    """Returns the Boolean value if given user with given course was denied for any
    incourse verification checkpoint.

    Args:
        user(User): user object
        course_id(CourseKey): CourseKey

    Returns:
        Boolean
    """
    return VerificationStatus.objects.filter(
        user=user,
        checkpoint__course_id=course_key,
        status='denied'
    ).exists()


def has_skipped_any_checkpoint(user, course_key):
    """Check existence of a user's skipped re-verification attempt for a
    specific course.

    Args:
        user(User): user object
        course_id(CourseKey): CourseKey

    Returns:
        Boolean
    """
    return SkippedReverification.check_user_skipped_reverification_exists(user, course_key)


def has_completed_checkpoint(user, course_key, checkpoint):
    """
    Get re-verification status against a user for a 'course_id' and checkpoint.
    Only approved and submitted status considered as completed.

    Args:
        user (User): The user whose status we are retrieving.
        course_key (CourseKey): The identifier for the course.
        checkpoint (UsageKey): The location of the checkpoint in the course.

    Returns:
        unicode or None
    """
    return VerificationStatus.check_user_has_completed_checkpoint(user, course_key, checkpoint)
