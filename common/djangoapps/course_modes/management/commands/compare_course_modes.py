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

    Run the following SQL against the ecommerce read replica:

    SELECT
        p.course_id,
        CASE
            WHEN a.value_text IS NULL THEN 'audit'
            WHEN a.value_text = 'professional' AND NOT b.value_boolean THEN 'no-id-professional'
            ELSE a.value_text
        END AS name,
        s.price_currency AS currency,
        CAST(s.price_excl_tax AS SIGNED) AS price,
        s.partner_sku AS sku,
        p.expires
    FROM
        catalogue_product p
    RIGHT JOIN
        partner_stockrecord s
        ON
            p.id = s.product_id
    LEFT JOIN catalogue_productattributevalue a
        ON
            s.product_id = a.product_id and
            a.attribute_id = 3
    LEFT JOIN catalogue_productattributevalue b
        ON
            s.product_id = b.product_id and
            b.attribute_id = 2
    ORDER BY course_id, sku;

    Copy the output into a CSV without the column headers

    Ensure that you are connected to the edx-platform read replica.

    Example:
      python ./manage.py lms compare_course_modes -f path/to/file.csv
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
        results = {}
        with open(options['filename'], 'rU') as csvfile:
            rows = csv.reader(csvfile, delimiter=',')
            for i, row in enumerate(rows):
                if i%100 == 0:
                    print i
                # clean row
                for j, cell in enumerate(row):
                    if cell == 'NULL':
                        row[j] = None

                # extract columns
                str_course_key = row[0]
                name = row[1]
                currency = row[2].lower()
                price = int(row[3])
                sku = row[4]

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

                results[str_course_key] = "Success"
                try:
                    course_mode = CourseMode.objects.get(course_id=course_key, mode_slug=name)
                except Exception as exception:
                    results[str_course_key] = "::{name}:: {msg}".format(name=name, msg=exception.message)
                    continue

                error_msg = ""
                if course_mode.mode_slug != name:
                    error_msg += "NAME CHANGED FROM [{old}] TO [{new}] ".format(old=course_mode.mode_slug, new=name)
                if course_mode.min_price != price:
                    error_msg += "PRICE CHANGED FROM [{old}] TO [{new}] ".format(old=course_mode.min_price, new=price)
                if course_mode.currency != currency:
                    error_msg += "CURRENCY CHANGED FROM [{old}] TO [{new}] ".format(old=course_mode.currency, new=currency)
                if course_mode.sku != sku:
                    error_msg += "SKU CHANGED FROM [{old}] TO [{new}] ".format(old=course_mode.sku, new=sku)

                if len(error_msg) > 0:
                    results[str_course_key] += " ::{name}:: {error}".format(name=course_mode.mode_slug,error=error_msg)

                error_courses = [key for key, val in results.items() if val != "Success"]

        for key in error_courses:
            print "{course}: {error}".format(course=key, error=results[key])
