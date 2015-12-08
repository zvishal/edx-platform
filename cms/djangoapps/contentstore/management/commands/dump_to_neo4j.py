import csv

from django.core.management.base import BaseCommand
from xmodule.modulestore.django import modulestore
from collections import defaultdict
import gc
import os


class Command(BaseCommand):
    """
    Generates CSVs to be used with neo4j's csv import tool (this is much
    faster for bulk importing than using py2neo, which updates neo4j over
    a REST api)
    """
    help = '''
    Here's an example neo4j-import command:

    ./bin/neo4j-import --id-type string --nodes:chapter chapter.csv \
    --nodes:discussion discussion.csv --nodes:html html.csv \
    --nodes:openassessment openassessment.csv
    --nodes:problem problem.csv \
    --nodes:sequential sequential.csv --nodes:vertical vertical.csv \
    --nodes:video video.csv --nodes:course course.csv \
    --relationships:PARENT_OF relationships.csv \
    --into data/coursegraph-demo \
    --multiline-fields=true

    (This could be refactored to automatically generate which nodes files
    to use based off of csv files present in a directory)
    '''

    # {<block_type>: [<field_name>]}
    field_names_by_type = {}


    def handle(self, *args, **options):

        all_courses = modulestore().get_courses()
        number_of_courses = len(all_courses)

        for index, course in enumerate(all_courses):
            # {<block_type>: [<block>]}
            blocks_by_type = defaultdict(list)

            relationships = []

            items = modulestore().get_items(course.id)
            print u"dumping {} (course {}/{}) ({} items)".format(
                course.id, index + 1, number_of_courses, len(items)
            )


            for item in items:

                # convert all fields to a dict and filter out parent field
                fields = dict(
                    (field, field_value.read_from(item))
                    for (field, field_value) in item.fields.iteritems()
                    if field not in ['parent', 'children']
                )

                fields['display_name'] = item.display_name_with_default

                if hasattr(item, 'course_id'):
                    fields['org'] = item.course_id.org
                    fields['course'] = item.course_id.course
                    fields['run'] = item.course_id.run
                    fields['course_id'] = unicode(item.course_id)

                fields['location:ID'] = unicode(item.location)
                if "location" in fields:
                    del fields['location']

                block_type = item.scope_ids.block_type

                fields['type'] = block_type

                fields['type:LABEL'] = fields['type']
                del fields['type']

                blocks_by_type[block_type].append(fields)



            for item in items:
                if item.has_children:
                    for child in item.children:
                        parent_loc = unicode(item.location)
                        child_loc = unicode(child)
                        relationships.append([parent_loc, child_loc])


            self.add_to_csvs_from_blocks(blocks_by_type)

            self.add_to_relationship_csv(relationships, index==0)

        print self.field_names_by_type.keys()

        print "DONE"


    def add_to_relationship_csv(self, relationships, create=False):
        rows = [[':START_ID', ':END_ID']] if create else []
        rows.extend(relationships)
        mode = 'w' if create else 'a'
        with open('/tmp/relationships.csv', mode) as csvfile:
            writer = UnicodeWriter(csvfile)
            writer.writerows(rows)


    def add_to_csvs_from_blocks(self, blocks_by_type):

        for block_type, fields_list in blocks_by_type.iteritems():
            create = False
            field_names = self.field_names_by_type.get(block_type)
            if field_names is None:
                field_names = fields_list[0].keys()
                field_names.remove('type:LABEL')
                field_names = ['type:LABEL'] + field_names
                self.field_names_by_type[block_type] = field_names
                create = True

            rows = [field_names] if create else []

            for fields in fields_list:
                row = [unicode(fields[field_name]) for field_name in field_names]
                rows.append(row)

            mode = 'w' if create else 'a'
            with open('/tmp/{}.csv'.format(block_type), mode) as csvfile:
                writer = UnicodeWriter(csvfile)
                writer.writerows(rows)








import csv, codecs, cStringIO

class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")

class UnicodeReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self

class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)