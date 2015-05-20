from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from openedx.core.djangoapps.credit.exceptions import InvalidCreditRequirements
from openedx.core.djangoapps.credit.models import CreditCourse, CreditRequirement


class ApiTestCases(ModuleStoreTestCase):
    """ Test for models """

    def setUp(self, **kwargs):
        super(ApiTestCases, self).setUp()
        self.course_key = CourseKey.from_string("edX/DemoX/Demo_Course")

    def test_set_credit_requirements(self):
        pass

    def test_get_credit_requirements(self):
        pass
