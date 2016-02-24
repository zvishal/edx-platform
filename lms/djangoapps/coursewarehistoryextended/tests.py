"""
Tests for coursewarehistoryextended
Many aspects of this app are covered by the courseware tests,
but these are specific to the new storage model with multiple
backend tables.
"""

import json
from mock import patch
from django.test import TestCase
from django.conf import settings
from unittest import skipUnless
from django.db.models import signals

from courseware.models import BaseStudentModuleHistory, StudentModuleHistory, StudentModule

from courseware.tests.factories import StudentModuleFactory, location, course_id
from student.tests.factories import UserFactory


@skipUnless(settings.FEATURES["ENABLE_CSMH_EXTENDED"], "CSMH Extended needs to be enabled")
class TestStudentModuleHistoryBackends(TestCase):
    """ Tests of data in CSMH and CSMHE """
    # Tell Django to clean out all databases, not just default
    multi_db = True

    def setUp(self):

        # This will store into CSMHE via the post_save signal
        csm = StudentModuleFactory(module_state_key=location('usage_id'),
                                   course_id=course_id,
                                   state=json.dumps({'type': 'csmhe'}))
        # This manually gets us a CSMH record to compare
        csmh = StudentModuleHistory(student_module=csm,
                                    version=None,
                                    created=csm.modified,
                                    state=json.dumps({'type': 'csmh'}),
                                    grade=csm.grade,
                                    max_grade=csm.max_grade)
        csmh.save()

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_CSMH_EXTENDED": True})
    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_READING_FROM_MULTIPLE_HISTORY_TABLES": True})
    def test_get_history_true_true(self):
        student_module = StudentModule.objects.all()
        history = BaseStudentModuleHistory.get_history(student_module)
        self.assertEquals(len(history), 2)
        self.assertEquals({'type': 'csmh'}, json.loads(history[0].state))
        self.assertEquals({'type': 'csmhe'}, json.loads(history[1].state))

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_CSMH_EXTENDED": True})
    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_READING_FROM_MULTIPLE_HISTORY_TABLES": False})
    def test_get_history_true_false(self):
        student_module = StudentModule.objects.all()
        history = BaseStudentModuleHistory.get_history(student_module)
        self.assertEquals(len(history), 1)
        self.assertEquals({'type': 'csmhe'}, json.loads(history[0].state))

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_CSMH_EXTENDED": False})
    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_READING_FROM_MULTIPLE_HISTORY_TABLES": True})
    def test_get_history_false_true(self):
        student_module = StudentModule.objects.all()
        history = BaseStudentModuleHistory.get_history(student_module)
        self.assertEquals(len(history), 1)
        self.assertEquals({'type': 'csmh'}, json.loads(history[0].state))

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_CSMH_EXTENDED": False})
    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_READING_FROM_MULTIPLE_HISTORY_TABLES": False})
    def test_get_history_false_false(self):
        student_module = StudentModule.objects.all()
        history = BaseStudentModuleHistory.get_history(student_module)
        self.assertEquals(len(history), 0)
