# -*- coding: utf-8 -*-
"""
Tests for In-Course Reverification Access Control Partition scheme
"""

from mock import Mock

from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.credit.partition_schemes import (
    VerificationPartitionScheme,
    is_enrolled_in_verified_mode,
    has_skipped_any_checkpoint,
    has_completed_checkpoint,
    was_denied_at_any_checkpoint
)
from student.models import CourseEnrollment

from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from lms.djangoapps.verify_student.models import (
    VerificationCheckpoint,
    VerificationStatus,
    SkippedReverification,
)


class ReverificationPartitionTest(ModuleStoreTestCase):
    """Tests for the Reverification Partition Scheme. """

    def setUp(self):
        super(ReverificationPartitionTest, self).setUp()
        self.user = UserFactory.create()
        self.course = CourseFactory.create()
        self.checkpoint_location = u'i4x://{org}/{course}/edx-reverification-block/first_uuid'.format(
            org=self.course.id.org, course=self.course.id.course
        )

        self.user_partition = Mock(user_partitions=[])
        self.user_partition.parameters = {
            "location": self.checkpoint_location
        }

        self.first_checkpoint = VerificationCheckpoint.objects.create(
            course_id=self.course.id,
            checkpoint_location=self.checkpoint_location
        )

        # now add verification status for multiple checkpoint points
        VerificationStatus.add_status_from_checkpoints(
            checkpoints=[self.first_checkpoint], user=self.user, status='submitted'
        )

        CourseEnrollment.objects.create(
            user=self.user,
            course_id=self.course.id,
            mode="verified",
            is_active=True
        )

        self.user_2 = UserFactory.create()
        self.non_existing_course = CourseKey.from_string('no/existing/Course')

        VerificationStatus.add_status_from_checkpoints(
            checkpoints=[self.first_checkpoint], user=self.user_2, status='denied'
        )

        CourseEnrollment.objects.create(
            user=self.user_2,
            course_id=self.course.id,
            mode="honor",
            is_active=True
        )

    def test_is_enrolled_in_verified_mode(self):
        self.assertTrue(
            is_enrolled_in_verified_mode(
                self.user, self.course.id
            )
        )

        self.assertFalse(
            is_enrolled_in_verified_mode(
                self.user_2, self.course.id
            )
        )

    def test_has_skipped_any_checkpoint(self):
        self.assertFalse(
            has_skipped_any_checkpoint(
                self.user, self.course.id
            )
        )

        # add skipped verification status for user
        SkippedReverification.add_skipped_reverification_attempt(
            checkpoint=self.first_checkpoint, user_id=self.user.id, course_id=self.course.id
        )
        self.assertTrue(
            has_skipped_any_checkpoint(
                self.user, self.course.id
            )
        )

    def test_user_has_completed_checkpoint(self):
        # user has completed the verification checkpoint ( either status is submitted or approved )
        self.assertTrue(
            has_completed_checkpoint(
                self.user, self.course.id, self.checkpoint_location
            )
        )

        # update the status to approved
        VerificationStatus.objects.filter(user=self.user).update(status='approved')
        self.assertTrue(
            has_completed_checkpoint(
                self.user, self.course.id, self.checkpoint_location
            )
        )

        # update the status to denied
        VerificationStatus.objects.filter(user=self.user).update(status='denied')
        self.assertFalse(
            has_completed_checkpoint(
                self.user, self.course.id, self.checkpoint_location
            )
        )

    def test_user_denied_at_any_checkpoint(self):
        # If user was denied at any checkpoint.

        self.assertTrue(
            was_denied_at_any_checkpoint(
                self.user_2, self.course.id
            )
        )

        self.assertFalse(
            was_denied_at_any_checkpoint(
                self.user_2, self.non_existing_course
            )
        )

    def test_get_group_for_user_with_completed_checkpoint(self):
        # If user is enrolled in verified mode and has completed any checkpoint

        self.assertEqual(
            VerificationPartitionScheme.VERIFIED_ALLOW,
            VerificationPartitionScheme.get_group_for_user(
                self.course.id,
                self.user,
                self.user_partition
            )
        )

    def test_get_group_for_user_with_skipped_checkpoint(self):
        # If user is enrolled in verified mode and skipped any checkpoint

        # add skipped verification status
        SkippedReverification.add_skipped_reverification_attempt(
            checkpoint=self.first_checkpoint, user_id=self.user.id, course_id=self.course.id
        )

        self.assertEqual(
            VerificationPartitionScheme.VERIFIED_ALLOW,
            VerificationPartitionScheme.get_group_for_user(
                self.course.id,
                self.user,
                self.user_partition
            )
        )

    def test_get_group_for_user_enrolled_in_non_verified_mode(self):
        # If user is enrolled in non verified mode

        self.assertEqual(
            VerificationPartitionScheme.NON_VERIFIED,
            VerificationPartitionScheme.get_group_for_user(
                self.course.id,
                self.user_2,
                self.user_partition
            )
        )

    def test_get_group_for_user_denied_at_any_checkpoint(self):
        # If user is denied at any checkpoint

        self.assertEqual(
            VerificationPartitionScheme.NON_VERIFIED,
            VerificationPartitionScheme.get_group_for_user(
                self.course.id,
                self.user_2,
                self.user_partition
            )
        )

    def test_get_group_for_verified_deny_groups(self):
        # If user is in verified mode but has no status attempt.

        # delete the user status records from db.
        VerificationStatus.objects.get(user=self.user).delete()
        self.assertEqual(
            VerificationPartitionScheme.VERIFIED_DENY,
            VerificationPartitionScheme.get_group_for_user(
                self.course.id,
                self.user,
                self.user_partition
            )
        )

    def test_key_for_partition(self):
        # Check it returns the valid key depending upon the location id.

        self.assertEqual(
            'verification:{}'.format(
                self.checkpoint_location
            ),
            VerificationPartitionScheme.key_for_partition(
                self.checkpoint_location
            )
        )
