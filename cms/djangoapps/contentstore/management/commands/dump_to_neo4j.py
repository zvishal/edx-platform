import json
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from django.conf import settings
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
import datetime

from django.contrib.auth.models import User
from student.models import CourseEnrollment

from py2neo import Graph, Node, Relationship, authenticate

def serialize_course(course):
    pass

class Command(BaseCommand):
    help = "Dump course items into a graph database"

    course_option = make_option(
        '--course',
        action='store',
        dest='course',
        default=False,
        help='--course <id> required, e.g. course-v1:org+course+run'
    )
    dump_all = make_option(
        '--all',
        action='store_true',
        dest='dump_all',
        default=False,
        help='dump all courses'
    )
    clear_all_first = make_option(
        '--clear-all-first',
        action='store_true',
        dest='clear_all_first',
        default=False,
        help='delete graph db before dumping'
    )

    option_list = BaseCommand.option_list + (course_option, dump_all, clear_all_first)

    def handle(self, *args, **options):
        graph = Graph(settings.NEO4J_URI)
        if options['clear_all_first']:
            print("deleting")
            graph.delete_all()

        if options['dump_all']:
            courses = modulestore().get_courses()
            node_map = {}
            for course in courses:
                print u'working on course ' + unicode(course.id)
                # first pass will create graph nodes and key-node mapping,
                # which will be used for searching in the second pass
                items = modulestore().get_items(course.id)
                course_node = None
                for item in items:
                    if 'detached' in item.runtime.load_block_type(item.category)._class_tags:
                        continue
                    # convert all fields to a dict and filter out parent field
                    fields = dict(
                        (field, field_value.read_from(item))
                        for (field, field_value) in item.fields.iteritems()
                        if field not in ['parent', 'children']
                    )
                    block_type = item.scope_ids.block_type
                    node = create_node(block_type, fields)
                    node_map[unicode(item.location)] = node
                    if block_type == 'course':
                        course_node = node
                graph.create(*node_map.values())

                # second pass
                relationships = []
                for item in items:
                    if 'detached' in item.runtime.load_block_type(item.category)._class_tags:
                        continue
                    if item.has_children:
                        for child in item.children:
                            relationship = Relationship(node_map[unicode(item.location)], 'PARENT_OF', node_map[unicode(child)])
                            relationships.append(relationship)
                graph.create(*relationships)

                # third pass
                enrollments = []
                for enrollment in CourseEnrollment.objects.filter(course_id=course.id):
                    user = enrollment.user
                    user_node = Node(
                        'student',
                        id=user.id,
                        name=user.profile.name,
                        gender=user.profile.gender,
                        year_of_birth=user.profile.year_of_birth,
                        level_of_education=user.profile.level_of_education,
                        country=unicode(user.profile.country)
                    )
                    if course_node:
                        enrollments.append(
                            Relationship(user_node, "ENROLLED_IN", course_node)
                        )
                graph.create(*enrollments)





def create_node(xblock_type, fields):
    for key, value in fields.iteritems():
        if isinstance(value, dict):
            fields[key] = json.dumps(value)
        elif isinstance(value, list):
            fields[key] = unicode(value)
        elif isinstance(value, datetime.timedelta):
            fields[key] = value.seconds
    try:
        node = Node('xblock', xblock_type, xblock_type=xblock_type, **fields)
    except:
        import pdb; pdb.set_trace()
        raise
    return node
