import ddt
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from openedx.core.djangoapps.credit.exceptions import InvalidCreditRequirements
from openedx.core.djangoapps.credit.models import CreditCourse, CreditRequirement


@ddt.ddt
class ModelTestCases(ModuleStoreTestCase):
    """ Test for models """

    def setUp(self, **kwargs):
        super(ModelTestCases, self).setUp()
        self.course_key = CourseKey.from_string("edX/DemoX/Demo_Course")

    @ddt.data(False, True)
    def test_is_credit_course(self, is_credit):
        if is_credit:
            CreditCourse(course_key=self.course_key).save()
            self.assertTrue(CreditCourse.is_credit_course(self.course_key))
        else:
            self.assertFalse(CreditCourse.is_credit_course(self.course_key))

    def test_get_credit_course_non_existence(self):
        with self.assertRaises(CreditCourse.DoesNotExist):
            CreditCourse.get_credit_course(self.course_key)

    def test_get_credit_course(self):
        credit_course = CreditCourse(course_key=self.course_key)
        credit_course.save()
        self.assertEquals(credit_course, CreditCourse.get_credit_course(self.course_key))

    def test_add_course_requirement_invalid_course(self):
        with self.assertRaises(InvalidCreditRequirements):
            requirement = {
                "namespace": "gade",
                "name": "grade",
                "configuration": {
                    "min_grade": 0.8
                }
            }
            CreditRequirement.add_course_requirement(None, requirement)

    def test_add_course_requirement_invalid_requirements(self):
        credit_course = CreditCourse(course_key=self.course_key)
        credit_course.save()
        with self.assertRaises(InvalidCreditRequirements):
            requirement = {
                "namespace": "gade",
                "name": "grade",
                "configuration": "invalid configuration"
            }
            CreditRequirement.add_course_requirement(credit_course, requirement)

    def test_add_course_requirement(self):
        credit_course = CreditCourse(course_key=self.course_key)
        credit_course.save()
        with self.assertRaises(InvalidCreditRequirements):
            requirement = {
                "namespace": "gade",
                "name": "grade",
                "configuration": "invalid configuration"
            }
            CreditRequirement.add_course_requirement(credit_course, requirement)
