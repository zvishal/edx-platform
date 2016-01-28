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

        rows = [["problems in course", "course", "course is open?"]]

        amount_of_courses = len(courses)

        for index, course in enumerate(courses):
            print "doing course \t{} / {}".format(index, amount_of_courses)

            number_of_dd = 0
            for item in ms.get_items(course.id, include_orphans=False):
                if item.category == 'problem':
                    try:
                        tree = etree.fromstring(item.data)
                    except etree.ParseError as error:
                        print unicode(error)
                        print "error parsing ", unicode(item)

                    for element in tree.getiterator():
                        if str(element.tag) == "drag_and_drop_input":
                            number_of_dd += 1

            row = [number_of_dd, unicode(course.id), not self.course_is_closed(course)]


            rows.append(row)

        print rows

        with open("/tmp/dd.csv", 'w') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(rows)


    def course_is_closed(self, course):
        if course.end is not None:
            return timezone.now() > course.end
        else:
            return False

