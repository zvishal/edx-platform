from opaque_keys.edx.keys import CourseKey
from courseware.courses import get_course_with_access
from edxnotes.helpers import (
    get_edxnotes_id_token,
    get_notes,
    is_feature_enabled,
    search,
    get_course_position,
    send_request,
    preprocess_collection
)
from django.contrib.auth.models import User
import cProfile

import json
from django.core.management.base import BaseCommand, CommandError
from django.core.urlresolvers import reverse

def notes(user_id, course_id):
    """
    Handles search requests.
    """
    course_key = CourseKey.from_string(course_id)
    user = User.objects.get(id=user_id)
    course = get_course_with_access(user, "load", course_key)

    response = send_request(user, course_id, "annotations")
    try:
        collection = json.loads(response.content)
    except ValueError:
        return None

    if not collection:
        return None

    preprocess_collection(user, course, collection)

class Command(BaseCommand):

    def handle(self, *args, **options):
        course_key = CourseKey.from_string("course-v1:edX+DemoX+Demo_Course")
        user = User.objects.get(id=5)
        course = get_course_with_access(user, "load", course_key)

        response = send_request(user, "course-v1:edX+DemoX+Demo_Course", "annotations")
        try:
            collection = json.loads(response.content)
        except ValueError:
            return None

        if not collection:
            return None

        profiler = cProfile.Profile()
        profiler.runcall(preprocess_collection, user, course, collection)
        profiler.print_stats(sort='cumulative')
        # profiler.sort_stats('cumulative').print_stats(100)
        # cProfile.run('import edxnotes; edxnotes.management.commands.notes.notes(5, "course-v1:edX+DemoX+Demo_Course")', 'notes_profile')
        # import pstats
        # p = pstats.Stats('notes_profile')
        # p.sort_stats('cumulative').print_stats(100)



def get_index(usage_key, children):
    """
    Returns an index of the child with `usage_key`.
    """
    children = [unicode(child) for child in children]
    return children.index(usage_key)


def get_module_context(course, item):
    """
    Returns dispay_name and url for the parent module.
    """
    item_dict = {
        'location': unicode(item.location),
        'display_name': item.display_name_with_default,
    }
    if item.category == 'chapter' and item.get_parent():
        # course is a locator w/o branch and version
        # so for uniformity we replace it with one that has them
        course = item.get_parent()
        item_dict['index'] = get_index(item_dict['location'], course.children)
    elif item.category == 'vertical':
        section = item.get_parent()
        chapter = section.get_parent()
        # Position starts from 1, that's why we add 1.
        position = get_index(unicode(item.location), section.children) + 1
        item_dict['url'] = reverse('courseware_position', kwargs={
            'course_id': unicode(course.id),
            'chapter': chapter.url_name,
            'section': section.url_name,
            'position': position,
        })
    if item.category in ('chapter', 'sequential'):
        item_dict['children'] = [unicode(child) for child in item.children]

    return item_dict
