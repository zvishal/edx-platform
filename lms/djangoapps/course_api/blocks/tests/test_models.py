"""
The models here
"""
from django.test import TestCase

from opaque_keys.edx.locator import CourseLocator

from ..models import CollectedCourseData


class TestCollectedCourseData(TestCase):

    COURSE_ID = CourseLocator(org="edX", course="Blocks101", run= "2015")
    COLLECTOR = "test.transform.collector"


    def test_removing_old_data(self):
        # Set three versions of the data and make sure they read out correctly.
        for collector_version in [1, 2, 3]:
            CollectedCourseData.set_data_for_course(
                course_key=self.COURSE_ID,
                content_version="abcde-make-no-order-assumptions",
                collector=self.COLLECTOR,
                collector_version=collector_version,
                data={"data_version": collector_version}
            )
            self.assertEqual(
                {"data_version": collector_version},
                CollectedCourseData.get_data_for_course(
                    course_id=self.COURSE_ID, collector=self.COLLECTOR, collector_version=collector_version
                )
            )

        # Version 2 should still be around (we keep the previous version alive)
        self.assertEqual(
            {"data_version": collector_version},
            CollectedCourseData.get_data_for_course(
                course_id=self.COURSE_ID, collector=self.COLLECTOR, collector_version=collector_version
            )
        )

        # But Version 1 should have been deleted
        with self.assertRaises(CollectedCourseData.DoesNotExist):
            CollectedCourseData.get_data_for_course(
                course_id=self.COURSE_ID, collector=self.COLLECTOR, collector_version=1
            )


    def test_set_data_old_versions(self):
        pass

