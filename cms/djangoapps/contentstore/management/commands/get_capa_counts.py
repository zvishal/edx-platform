import csv

from django.core.management.base import BaseCommand
from xmodule.modulestore.django import modulestore
from collections import defaultdict

from django.utils import timezone

from lxml import etree


class Command(BaseCommand):

    def handle(self, *args, **options):

        ms = modulestore()._get_modulestore_by_type('split')

        courses = ms.get_courses()

        inputtypes = defaultdict(lambda: defaultdict(set))

        amount_of_courses = len(courses)

        for index, course in enumerate(courses):
            print "doing course \t{} / {}".format(index, amount_of_courses)
            if self.course_is_closed(course):
                print "{} is closed".format(course.id)
                continue

            for item in ms.get_items(course.id, include_orphans=False):
                if item.category == 'problem':
                    try:
                        tree = etree.fromstring(item.data)
                    except etree.ParseError as error:
                        print unicode(error)

                    for element in tree.getiterator():
                        if self.is_input(str(element.tag)):
                            inputtypes[element.tag]['courses'].add(
                                course.id
                            )
                            inputtypes[element.tag]['problems'].add(
                                item.location
                            )

            rows = [["inputtype", "number of courses", "number of problems"]]
            for inputtype in inputtypes:
                row = [inputtype, len(inputtypes[inputtype]['courses']), len(inputtypes[inputtype]['problems'])]
                rows.append(row)

            with open("/tmp/capa.csv", 'w') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(rows)



    def course_is_closed(self, course):
        if course.end is not None:
            return timezone.now() > course.end
        else:
            return False


    def is_tag(self, tag):
        return tag.endswith('response')

    def is_input(self, tag):
        try:
            if tag.endswith('input') or tag.endswith('group'):
                return True
        except AttributeError:
            print tag

        if tag in [
            "textline",
            'crystallography',
            'filesubmission',
            'textbox',
            'schematic',
        ]:
            return True

        return False


