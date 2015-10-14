import json
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from django.conf import settings
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore

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
            for course in courses:
                print u'working on course ' + unicode(course.id)
                # first pass will create graph nodes and key-node mapping,
                # which will be used for searching in the second pass
                node_map = {}
                items = modulestore().get_items(course.id)
                for item in items:
                    if 'detached' in item.runtime.load_block_type(item.category)._class_tags:
                        continue
                    # convert all fields to a dict and filter out parent field
                    fields = dict(
                        [(field, field_value.read_from(item))
                         for (field, field_value) in item.fields.iteritems()
                         if field != 'parent' and field != 'children'])
                    node = create_node(item.scope_ids.block_type, fields)
                    node_map[unicode(item.location)] = node
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


def create_node(xblock_type, fields):
    for key, value in fields.iteritems():
        if isinstance(value, dict):
            fields[key] = json.dumps(value)
        elif isinstance(value, list):
            fields[key] = unicode(value)
    try:
        node = Node('xblock', xblock_type, xblock_type=xblock_type, **fields)
    except:
        import pdb; pdb.set_trace()
        raise
    return node
