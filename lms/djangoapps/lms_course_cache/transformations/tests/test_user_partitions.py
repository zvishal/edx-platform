"""
Tests for UserPartitionTransformation.
"""

from openedx.core.djangoapps.user_api.partition_schemes import RandomUserPartitionScheme
from openedx.core.djangoapps.course_groups.partition_scheme import CohortPartitionScheme
from openedx.core.djangoapps.course_groups.tests.helpers import CohortFactory, config_course_cohorts
from openedx.core.djangoapps.course_groups.cohorts import add_user_to_cohort
from openedx.core.djangoapps.course_groups.views import link_cohort_to_partition_group
from opaque_keys.edx.keys import CourseKey
from student.tests.factories import UserFactory
from student.tests.factories import CourseEnrollmentFactory
from xmodule.modulestore.django import modulestore
from xmodule.partitions.partitions import Group, UserPartition

from lms_course_cache.transformations.user_partitions import UserPartitionTransformation, SplitTestTransformation
from lms_course_cache.api import get_course_blocks, clear_course_from_cache
from test_helpers import CourseStructureTestCase

from lms_course_cache.transformations.helpers import get_user_partition_groups


class UserPartitionTransformationTestCase(CourseStructureTestCase):
    """
    ...
    """

    def setUp(self):
        super(UserPartitionTransformationTestCase, self).setUp()

        # Set up user partitions and groups.
        self.groups = [Group(1, 'Group 1'), Group(2, 'Group 2')]
        self.content_groups = [1, 2]
        self.user_partition = UserPartition(
            id=0,
            name='Partition 1',
            description='This is partition 1',
            groups=self.groups,
            scheme=CohortPartitionScheme
        )
        self.user_partition.scheme.name = "cohort"

        # Build course.
        self.course_hierarchy = self.get_test_course_hierarchy()
        self.blocks = self.build_course(self.course_hierarchy)
        self.course = self.blocks['course']
        clear_course_from_cache(self.course.id)

        # Set up user and enroll in course.
        self.password = 'test'
        self.user = UserFactory.create(password=self.password)
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id, is_active=True)

        # Set up cohorts.
        config_course_cohorts(self.course, is_cohorted=True)
        self.cohorts = [CohortFactory(course_id=self.course.id) for __ in enumerate(self.groups)]

    def get_test_course_hierarchy(self):
        """
        Get a course hierarchy to test with.

        Assumes self.user_partition has already been initialized.
        """
        return {
            'org': 'UserPartitionTransformation',
            'course': 'UP101F',
            'run': 'test_run',
            'user_partitions': [self.user_partition],
            '#ref': 'course',
            '#children': [
                {
                    '#type': 'chapter',
                    '#ref': 'chapter1',
                    '#children': [
                        {
                            'metadata': {
                                'group_access': {0: [0, 1, 2]},
                            },
                                '#type': 'sequential',
                                '#ref': 'lesson1',
                            '#children': [
                                {
                                    '#type': 'vertical',
                                    '#ref': 'vertical1',
                                    '#children': [
                                        {
                                            'metadata': {'group_access': {0: [0]}},
                                            '#type': 'html',
                                            '#ref': 'html1',
                                        },
                                        {
                                            'metadata': {'group_access': {0: [1]}},
                                            '#type': 'html',
                                            '#ref': 'html2',
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ]
        }

    def add_user_to_cohort_group(self, cohort_index, group_id=None):
        """
        Add user to cohort, link cohort to content group, and update blocks.
        """
        add_user_to_cohort(self.cohorts[cohort_index], self.user.username)
        if not group_id:
            group_id = self.groups[cohort_index].id
        link_cohort_to_partition_group(
            self.cohorts[cohort_index],
            self.user_partition.id,
            group_id,
        )
        store = modulestore()
        for __, block in self.blocks.iteritems():
            block.save()
            store.update_item(block, self.user.id)

    def get_block_key_set(self, *refs):
        """
        Gets the set of usage keys that correspond to the list of
        #ref values as defined on self.blocks.

        Returns: set[UsageKey]
        """
        xblocks = (self.blocks[ref] for ref in refs)
        return set([xblock.location for xblock in xblocks])

    def test_course_structure_with_user_partition_not_enrolled(self):
        self.transformation = UserPartitionTransformation()

        __, raw_data_blocks = get_course_blocks(
            self.user,
            self.course.id,
            transformations={}
        )
        self.assertEqual(len(raw_data_blocks), len(self.blocks))

        clear_course_from_cache(self.course.id)
        __, trans_data_blocks = get_course_blocks(
            self.user,
            self.course.id,
            transformations={self.transformation}
        )
        self.assertEqual(
            set(trans_data_blocks.keys()),
            self.get_block_key_set('course', 'chapter1')
        )

    def test_course_structure_with_user_partition_enrolled(self):
        self.add_user_to_cohort_group(0, 2)
        self.transformation = UserPartitionTransformation()

        __, raw_data_blocks = get_course_blocks(
            self.user,
            self.course.id,
            transformations={}
        )
        self.assertEqual(len(raw_data_blocks), len(self.blocks))

        clear_course_from_cache(self.course.id)
        __, trans_data_blocks = get_course_blocks(
            self.user,
            self.course.id,
            transformations={self.transformation}
        )
        self.assertEqual(
            set(trans_data_blocks.keys()),
            self.get_block_key_set('course', 'chapter1', 'lesson1', 'vertical1')
        )

    def test_course_structure_with_user_partition_enrolled_visible_html(self):
        self.add_user_to_cohort_group(0)
        self.transformation = UserPartitionTransformation()

        __, raw_data_blocks = get_course_blocks(
            self.user,
            self.course.id,
            transformations={}
        )
        self.assertEqual(len(raw_data_blocks), len(self.blocks))

        clear_course_from_cache(self.course.id)
        __, trans_data_blocks = get_course_blocks(
            self.user,
            self.course.id,
            transformations={self.transformation}
        )
        self.assertEqual(
            set(trans_data_blocks.keys()),
            self.get_block_key_set('course', 'chapter1', 'lesson1', 'vertical1', 'html2')
        )


class SplitTestTransformationTestCase(CourseStructureTestCase):
    """
    ...
    """

    def setUp(self):
        super(SplitTestTransformationTestCase, self).setUp()

        # Set up user partitions and groups.
        self.groups = [Group(3, 'Group A'), Group(4, 'Group B')]
        self.content_groups = [3, 4]
        self.split_test_user_partition = UserPartition(
            id=0,
            name='Partition 2',
            description='This is partition 2',
            groups=self.groups,
            scheme=RandomUserPartitionScheme
        )
        self.split_test_user_partition.scheme.name = "random"

        # Build course.
        self.course_hierarchy = self.get_test_course_hierarchy()
        self.blocks = self.build_course(self.course_hierarchy)
        self.course = self.blocks['course']
        clear_course_from_cache(self.course.id)

        # Set up user and enroll in course.
        self.password = 'test'
        self.user = UserFactory.create(password=self.password)
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id, is_active=True)

    def get_test_course_hierarchy(self):
        """
        Get a course hierarchy to test with.

        Assumes self.user_partition has already been initialized.
        """
        return {
            'org': 'SplitTestTransformation',
            'course': 'ST101F',
            'run': 'test_run',
            'user_partitions': [self.split_test_user_partition],
            '#ref': 'course',
            '#children': [
                {
                    '#type': 'chapter',
                    '#ref': 'chapter1',
                    '#children': [
                        {
                                '#type': 'sequential',
                                '#ref': 'lesson1',
                            '#children': [
                                {
                                    '#type': 'vertical',
                                    '#ref': 'vertical1',
                                    '#children': [
                                        {
                                            'metadata': {'category': 'split_test'}, 
                                            'user_partition_id': 0,
                                            'group_id_to_child': {
                                                "3": "i4x://SplitTestTransformation/ST101F/vertical/vertical_vertical2",
                                                "4": "i4x://SplitTestTransformation/ST101F/vertical/vertical_vertical3"
                                            },
                                            '#type': 'split_test',
                                            '#ref': 'split_test1',
                                            '#children': [
                                                {
                                                    'metadata': {'display_name': "Group ID 3"},
                                                    '#type': 'vertical',
                                                    '#ref': 'vertical2',
                                                    '#children': [
                                                        {
                                                            'metadata': {'display_name': "Group A"},
                                                            '#type': 'html',
                                                            '#ref': 'html1',
                                                        }
                                                    ]
                                                }, 
                                                {
                                                    'metadata': {'display_name': "Group ID 4"},
                                                    '#type': 'vertical',
                                                    '#ref': 'vertical3',
                                                    '#children': [
                                                        {
                                                            'metadata': {'display_name': "Group A"},
                                                            '#type': 'html',
                                                            '#ref': 'html2',
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ]
        }

    def add_user_to_splittest_group(self, assign=True):
        """
        Add user to split test, get group for him and update blocks.
        """
        self.split_test_user_partition.scheme.get_group_for_user(
            CourseKey.from_string(unicode(self.course.id)),
            self.user,
            self.split_test_user_partition,
            assign=assign,
        )
        store = modulestore()
        for __, block in self.blocks.iteritems():
            block.save()
            store.update_item(block, self.user.id)

    def get_block_key_set(self, *refs):
        """
        Gets the set of usage keys that correspond to the list of
        #ref values as defined on self.blocks.

        Returns: set[UsageKey]
        """
        xblocks = (self.blocks[ref] for ref in refs)
        return set([xblock.location for xblock in xblocks])

    def test_course_structure_with_user_split_test(self):
        self.transformation = SplitTestTransformation()

        # Add user to split test.
        self.add_user_to_splittest_group(assign=False)

        __, raw_data_blocks = get_course_blocks(
            self.user,
            self.course.id,
            transformations={}
        )
        self.assertEqual(len(raw_data_blocks), len(self.blocks))

        clear_course_from_cache(self.course.id)
        __, trans_data_blocks = get_course_blocks(
            self.user,
            self.course.id,
            transformations={self.transformation}
        )

        user_groups = get_user_partition_groups(
            self.course.id, [self.split_test_user_partition], self.user
        )

        self.assertEqual(
            set(trans_data_blocks.keys()),
            self.get_block_key_set('course', 'chapter1', 'lesson1', 'vertical1', 'split_test1')
        )

    def test_course_structure_with_user_split_test_group_assigned(self):
        self.transformation = SplitTestTransformation()

        # Add user to split test.
        self.add_user_to_splittest_group()

        __, raw_data_blocks = get_course_blocks(
            self.user,
            self.course.id,
            transformations={}
        )
        self.assertEqual(len(raw_data_blocks), len(self.blocks))

        clear_course_from_cache(self.course.id)
        __, trans_data_blocks = get_course_blocks(
            self.user,
            self.course.id,
            transformations={self.transformation}
        )

        user_groups = get_user_partition_groups(
            self.course.id, [self.split_test_user_partition], self.user
        )
        for group in user_groups.itervalues():
            if group.id == 3:
                self.assertEqual(
                    set(trans_data_blocks.keys()),
                    self.get_block_key_set('course', 'chapter1', 'lesson1', 'vertical1', 'split_test1', 'vertical2', 'html1')
                )
            else:
                self.assertEqual(
                    set(trans_data_blocks.keys()),
                    self.get_block_key_set('course', 'chapter1', 'lesson1', 'vertical1', 'split_test1', 'vertical3', 'html2')
                )
