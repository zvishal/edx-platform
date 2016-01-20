"""
Management command to compare a csv of what coursemodes OTTO would publish to LMS against
what is currently in the LMS DB.
"""
import csv

from django.core.management.base import BaseCommand
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from optparse import make_option

from course_modes.models import CourseMode

class Command(BaseCommand):

    help = """
    Example:
      sudo -u www-data SERVICE_VARIANT=lms /opt/edx/bin/django-admin.py get_grades \
        -c MITx/Chi6.00intro/A_Taste_of_Python_Programming -o /tmp/20130813-6.00x.csv \
        --settings=lms.envs.aws --pythonpath=/opt/wwc/edx-platform
    """

    option_list = BaseCommand.option_list + (
        make_option('-f', '--filename',
                    metavar='FILENAME',
                    dest='filename',
                    default=False,
                    help='CSV file of OTTO data'),
        make_option('-o', '--output',
                    metavar='FILE',
                    dest='output',
                    default=False,
                    help='Filename for grade output'))

    def handle(self, *args, **options):
        with open(options['filename'], 'rU') as csvfile:
            rows = csv.reader(csvfile, delimiter=',')
            for i, row in enumerate(rows):
                if i%100 == 0:
                    print i
                # extract columns
                str_course_key = row[0]
                course_mode_count = int(row[1])

                # parse out the course into a coursekey
                if str_course_key:
                    try:
                        course_key = CourseKey.from_string(str_course_key)
                    # if it's not a new-style course key, parse it from an old-style
                    # course key
                    except InvalidKeyError:
                        try:
                            course_key = SlashSeparatedCourseKey.from_deprecated_string(str_course_key)
                        except InvalidKeyError:
                            print "Error finding course: {course}".format(course=row[0])
                            continue
                else:
                    print "Error finding course: {course}".format(course=row[0])
                    continue

                try:
                    course_modes = CourseMode.objects.filter(course_id=course_key)
                    if len(course_modes) != course_mode_count:
                        print "{key}: OTTO has {otto} seats, LMS has {lms} modes".format(
                            key=str_course_key,
                            otto=course_mode_count,
                            lms=len(course_modes)
                        )
                except Exception as exception:
                    print "{msg}".format(msg=exception.message)
                    continue
