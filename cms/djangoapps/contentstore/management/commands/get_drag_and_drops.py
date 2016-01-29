import csv
import gc

from django.core.management.base import BaseCommand
from xmodule.modulestore.django import modulestore
from collections import defaultdict

from django.utils import timezone

from lxml import etree
import objgraph


class Command(BaseCommand):

    def handle(self, *args, **options):

        ms = modulestore()

        courses = ms.get_courses()

        rows = [["problems in course", "course", "course is open?"]]

        amount_of_courses = len(courses)

        objgraph.show_growth()

        for index, course in enumerate(courses):
            print "doing course \t{} / {}: {}".format(index, amount_of_courses, course.id)

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

            if number_of_dd:
                row = [number_of_dd, unicode(course.id), not self.course_is_closed(course)]
                rows.append(row)

        with open("/tmp/dd.csv", 'w') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(rows)

        course = None
        rows = None
        gc.collect()

        objgraph.show_growth(100)


    def course_is_closed(self, course):
        if course.end is not None:
            return timezone.now() > course.end
        else:
            return False

