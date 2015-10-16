"""
Tests for block_cache.py


def transform(user_info, structure, collected_data):
    field_values = collected_data.xblock_field_values



"""
from mock import patch
from unittest import TestCase

from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys.edx.locator import CourseLocator, LibraryLocator, BlockUsageLocator

from .test_utils import (
    MockModulestoreFactory, MockCache, MockUserInfo, MockTransformer, ChildrenMapTestMixin
)
from ..block_cache import get_blocks
from ..bcu import BlockCacheUnit, BlockFieldValues, BlockIndexMapping, CollectionData


TEST_COURSE_KEY = CourseLocator(org="BCU", course="Fast", run="101")


class TestBlockCacheUnit(TestCase):

    def setUp(self):
        self.bcu = BlockCacheUnit(
            block_structure,
            xblock_field_values,
            transformers_to_field_values,
            transformers_to_data,
        )

class TestBlockFieldValues(TestCase):

    def setUp(self):
        self.mapping = BlockIndexMapping(
            make_locators(TEST_COURSE_KEY, chapter=2, vertical=2, html=5, problem=5)
        )
        self.field_values = BlockFieldValues(
            self.mapping,
            {
                'block_id': [key.block_id for key in self.mapping],
                'block_type': [key.block_type for key in self.mapping],
                'has_score': [key.block_type == 'problem' for key in self.mapping],
                'horribly_named': [key.block_type == 'vertical' for key in self.mapping],
            }
        )

    def test_get(self):
        # Check some values we expect
        self.assertEqual(
            'chapter',
            self.field_values.get('block_type', BlockUsageLocator(TEST_COURSE_KEY, 'chapter', 'chapter_0'))
        )
        self.assertEqual(
            'html_4',
            self.field_values.get('block_id', BlockUsageLocator(TEST_COURSE_KEY, 'html', 'html_4'))
        )
        self.assertTrue(
            self.field_values.get('horribly_named', BlockUsageLocator(TEST_COURSE_KEY, 'vertical', 'vertical_1'))
        )
        self.assertEqual(
            self.field_values[BlockUsageLocator(TEST_COURSE_KEY, 'problem', 'problem_4')],
            {
                'block_type': 'problem',
                'block_id': 'problem_4',
                'has_score': True,
                'horribly_named': False,
            }
        )
        # Make sure we throw key errors for non-existent fields or block keys
        with self.assertRaises(KeyError):
            self.field_values.get('no_such_field', BlockUsageLocator(TEST_COURSE_KEY, 'html', 'html_1'))
        with self.assertRaises(KeyError):
            self.field_values.get('block_id', TEST_COURSE_KEY)

    def test_slice_by_fields(self):
        self.assertEqual(
            ['block_id', 'block_type', 'has_score', 'horribly_named'],
            self.field_values.fields
        )
        chapter_key = BlockUsageLocator(TEST_COURSE_KEY, 'chapter', 'chapter_0')

        empty = self.field_values.slice_by_fields([])
        self.assertEqual([], empty.fields)
        self.assertEqual({}, empty[chapter_key])

        grading = self.field_values.slice_by_fields(['block_id', 'has_score'])
        self.assertEqual(
            {'block_id': 'chapter_0', 'has_score': False},
            grading[chapter_key]
        )
        self.assertEqual('chapter_0', grading.get('block_id', chapter_key))

        # Now test mutation -- these are supposed to point to the same underlying
        # lists (or XBlock field mutations wouldn't carry across Transformers)
        self.assertFalse(grading.get('has_score', chapter_key))
        self.assertFalse(self.field_values.get('has_score', chapter_key))
        grading.set('has_score', chapter_key, True)
        self.assertTrue(grading.get('has_score', chapter_key))
        self.assertTrue(self.field_values.get('has_score', chapter_key))


class TestBlockIndexMapping(TestCase):

    def setUp(self):
        self.locators = make_locators(
            TEST_COURSE_KEY, chapter=2, vertical=3, html=5, problem=5, video=5
        )
        self.mapping = BlockIndexMapping(self.locators)

    def test_locator_ordering(self):
        """Locators should iterate in sorted order."""
        sorted_locators = sorted(self.locators)
        self.assertEqual(sorted_locators, list(self.mapping))

    def test_index_lookup(self):
        self.assertEqual(0, self.mapping.index_for(BlockUsageLocator(TEST_COURSE_KEY, 'chapter', 'chapter_0')))
        self.assertEqual(2, self.mapping.index_for(BlockUsageLocator(TEST_COURSE_KEY, 'course', '2015')))
        self.assertEqual(20, self.mapping.index_for(BlockUsageLocator(TEST_COURSE_KEY, 'video', 'video_4')))
        with self.assertRaises(KeyError):
            self.mapping.index_for(TEST_COURSE_KEY)


def make_locators(course_key, **block_types_to_qty):
    locators = [BlockUsageLocator(TEST_COURSE_KEY, 'course', '2015')]
    for block_type, qty in block_types_to_qty.items():
        for i in xrange(qty):
            block_id = "{}_{}".format(block_type, i)
            locators.append(BlockUsageLocator(TEST_COURSE_KEY, block_type, block_id))
    return locators
