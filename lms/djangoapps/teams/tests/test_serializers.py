# -*- coding: utf-8 -*-
"""
Tests for custom Teams Serializers.
"""
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from lms.djangoapps.teams.tests.factories import CourseTeamFactory
from lms.djangoapps.teams.serializers import BaseTopicSerializer, TopicSerializer


class TopicTestCase(ModuleStoreTestCase):
    """
    Base test class to set up a course with topics
    """
    def setUp(self):
        """
        Set up a course with a teams configuration.
        """
        super(TopicTestCase, self).setUp()
        self.course = CourseFactory.create(
            teams_configuration={
                "max_team_size": 10,
                "topics": [{u'name': u'Tøpic', u'description': u'The bést topic!', u'id': u'0'}]
            }
        )


class BaseTopicSerializerTestCase(TopicTestCase):
    """
    Tests for the `BaseTopicSerializer`, which should not serialize team count
    data.
    """
    def test_team_count_not_included(self):
        """Verifies that the `BaseTopicSerializer` does not include team count"""
        with self.assertNumQueries(0):
            serializer = BaseTopicSerializer(self.course.teams_topics[0])
            self.assertEqual(
                serializer.data,
                {u'name': u'Tøpic', u'description': u'The bést topic!', u'id': u'0'}
            )


class TopicSerializerTestCase(TopicTestCase):
    """
    Tests for the `TopicSerializer`, which should serialize team count data for
    a single topic.
    """
    def test_topic_with_no_team_count(self):
        """
        Verifies that the `TopicSerializer` correctly displays a topic with a
        team count of 0, and that it only takes one SQL query.
        """
        with self.assertNumQueries(1):
            serializer = TopicSerializer(self.course.teams_topics[0], context={'course_id': self.course.id})
            self.assertEqual(
                serializer.data,
                {u'name': u'Tøpic', u'description': u'The bést topic!', u'id': u'0', u'team_count': 0}
            )

    def test_topic_with_team_count(self):
        """
        Verifies that the `TopicSerializer` correctly displays a topic with a
        positive team count, and that it only takes one SQL query.
        """
        CourseTeamFactory.create(course_id=self.course.id, topic_id=self.course.teams_topics[0]['id'])
        with self.assertNumQueries(1):
            serializer = TopicSerializer(self.course.teams_topics[0], context={'course_id': self.course.id})
            self.assertEqual(
                serializer.data,
                {u'name': u'Tøpic', u'description': u'The bést topic!', u'id': u'0', u'team_count': 1}
            )

    def test_scoped_within_course(self):
        """Verify that team count is scoped within a course."""
        duplicate_topic = self.course.teams_topics[0]
        second_course = CourseFactory.create(
            teams_configuration={
                "max_team_size": 10,
                "topics": [duplicate_topic]
            }
        )
        CourseTeamFactory.create(course_id=self.course.id, topic_id=duplicate_topic[u'id'])
        CourseTeamFactory.create(course_id=second_course.id, topic_id=duplicate_topic[u'id'])
        with self.assertNumQueries(1):
            serializer = TopicSerializer(self.course.teams_topics[0], context={'course_id': self.course.id})
            self.assertEqual(
                serializer.data,
                {u'name': u'Tøpic', u'description': u'The bést topic!', u'id': u'0', u'team_count': 1}
            )
