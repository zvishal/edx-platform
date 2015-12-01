import csv

from django.core.management.base import BaseCommand
from xmodule.modulestore.django import modulestore
from collections import defaultdict


class Command(BaseCommand):
    """
    """
    help = '''
    '''

    def handle(self, *args, **options):



        blocks_by_type = defaultdict(list)

        location_fields_map = {}

        relationships = [[':START_ID', ':END_ID']]

        for course in modulestore().get_courses():
            items = modulestore().get_items(course.id)
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
                fields['location'] = unicode(item.location)

                block_type = item.scope_ids.block_type

                fields['type'] = block_type

                location_fields_map[item.location] = fields

                blocks_by_type[block_type].append(fields)



            for item in items:
                if item.has_children:
                    for child in item.children:
                        parent_loc = unicode(item.location)
                        child_loc = unicode(child)
                        relationships.append([parent_loc, child_loc])


        self.make_csvs_from_blocks(blocks_by_type)

        self.make_relationship_csv(relationships)

        return


    def make_relationship_csv(self, relationships):
        with open('/tmp/relationships.csv', 'w') as csvfile:
            writer = UnicodeWriter(csvfile)
            writer.writerows(relationships)


    def make_csvs_from_blocks(self, blocks_by_type):

        for block_type, fields_list in blocks_by_type.iteritems():
            field_names = fields_list[0].keys()
            field_names.remove('location')
            rows = ["location:ID"] + field_names
            for fields in fields_list:
                row = [fields['location']]
                row.extend([unicode(fields[field_name]) for field_name in field_names])
                rows.append(row)

            with open('/tmp/{}.csv'.format(block_type), 'w') as csvfile:
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