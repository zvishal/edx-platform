"""Tests covering Programs utilities."""
import unittest

from django.conf import settings
from django.core.cache import cache
from django.test import TestCase
import httpretty
import mock
from edx_oauth2_provider.tests.factories import ClientFactory
from provider.constants import CONFIDENTIAL

from openedx.core.djangoapps.credentials.tests.mixins import CredentialsApiConfigMixin
from openedx.core.djangoapps.programs.models import ProgramsApiConfig
from openedx.core.djangoapps.programs.tests.mixins import ProgramsApiConfigMixin, ProgramsDataMixin
from openedx.core.djangoapps.programs.utils import (
    get_programs, get_programs_for_credentials, get_programs_for_dashboard
)
from student.tests.factories import UserFactory


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestProgramRetrieval(ProgramsApiConfigMixin, ProgramsDataMixin,
                           CredentialsApiConfigMixin, TestCase):
    """Tests covering the retrieval of programs from the Programs service."""
    def setUp(self):
        super(TestProgramRetrieval, self).setUp()

        ClientFactory(name=ProgramsApiConfig.OAUTH2_CLIENT_NAME, client_type=CONFIDENTIAL)
        self.user = UserFactory()

        cache.clear()

    @httpretty.activate
    def test_get_programs(self):
        """Verify programs data can be retrieved."""
        self.create_programs_config()
        self.mock_programs_api()

        actual = get_programs(self.user)
        self.assertEqual(
            actual,
            self.PROGRAMS_API_RESPONSE['results']
        )

        # Verify the API was actually hit (not the cache).
        self.assertEqual(len(httpretty.httpretty.latest_requests), 1)

    @httpretty.activate
    def test_get_programs_caching(self):
        """Verify that when enabled, the cache is used for non-staff users."""
        self.create_programs_config(cache_ttl=1)
        self.mock_programs_api()

        # Warm up the cache.
        get_programs(self.user)

        # Hit the cache.
        get_programs(self.user)

        # Verify only one request was made.
        self.assertEqual(len(httpretty.httpretty.latest_requests), 1)

        staff_user = UserFactory(is_staff=True)

        # Hit the Programs API twice.
        for _ in range(2):
            get_programs(staff_user)

        # Verify that three requests have been made (one for student, two for staff).
        self.assertEqual(len(httpretty.httpretty.latest_requests), 3)

    def test_get_programs_programs_disabled(self):
        """Verify behavior when programs is disabled."""
        self.create_programs_config(enabled=False)

        actual = get_programs(self.user)
        self.assertEqual(actual, [])

    @mock.patch('edx_rest_api_client.client.EdxRestApiClient.__init__')
    def test_get_programs_client_initialization_failure(self, mock_init):
        """Verify behavior when API client fails to initialize."""
        self.create_programs_config()
        mock_init.side_effect = Exception

        actual = get_programs(self.user)
        self.assertEqual(actual, [])
        self.assertTrue(mock_init.called)

    @httpretty.activate
    def test_get_programs_data_retrieval_failure(self):
        """Verify behavior when data can't be retrieved from Programs."""
        self.create_programs_config()
        self.mock_programs_api(status_code=500)

        actual = get_programs(self.user)
        self.assertEqual(actual, [])

    @httpretty.activate
    def test_get_programs_for_dashboard(self):
        """Verify programs data can be retrieved and parsed correctly."""
        self.create_programs_config()
        self.mock_programs_api()

        actual = get_programs_for_dashboard(self.user, self.COURSE_KEYS)
        expected = {}
        for program in self.PROGRAMS_API_RESPONSE['results']:
            for course_code in program['course_codes']:
                for run in course_code['run_modes']:
                    course_key = run['course_key']
                    expected[course_key] = program

        self.assertEqual(actual, expected)

    def test_get_programs_for_dashboard_dashboard_display_disabled(self):
        """Verify behavior when student dashboard display is disabled."""
        self.create_programs_config(enable_student_dashboard=False)

        actual = get_programs_for_dashboard(self.user, self.COURSE_KEYS)
        self.assertEqual(actual, {})

    @httpretty.activate
    def test_get_programs_for_dashboard_no_data(self):
        """Verify behavior when no programs data is found for the user."""
        self.create_programs_config()
        self.mock_programs_api(data={'results': []})

        actual = get_programs_for_dashboard(self.user, self.COURSE_KEYS)
        self.assertEqual(actual, {})

    @httpretty.activate
    def test_get_programs_for_dashboard_invalid_data(self):
        """Verify behavior when the Programs API returns invalid data and parsing fails."""
        self.create_programs_config()
        invalid_program = {'invalid_key': 'invalid_data'}
        self.mock_programs_api(data={'results': [invalid_program]})

        actual = get_programs_for_dashboard(self.user, self.COURSE_KEYS)
        self.assertEqual(actual, {})

    @httpretty.activate
    def test_get_program_for_certificates(self):
        """Verify programs data can be retrieved and parsed correctly for certificates."""
        self.create_programs_config()
        self.mock_programs_api()

        actual = get_programs_for_credentials(self.user, self.PROGRAMS_CREDENTIALS_DATA)
        expected = self.PROGRAMS_API_RESPONSE['results']
        expected[0]['credential_url'] = self.PROGRAMS_CREDENTIALS_DATA[0]['certificate_url']
        expected[1]['credential_url'] = self.PROGRAMS_CREDENTIALS_DATA[1]['certificate_url']

        self.assertEqual(len(actual), 2)
        self.assertEqual(actual, expected)

    @httpretty.activate
    def test_get_program_for_certificates_no_data(self):
        """Verify behavior when no programs data is found for the user."""
        self.create_programs_config()
        self.create_credentials_config()
        self.mock_programs_api(data={'results': []})

        actual = get_programs_for_credentials(self.user, self.PROGRAMS_CREDENTIALS_DATA)
        self.assertEqual(actual, [])

    @httpretty.activate
    def test_get_program_for_certificates_id_not_exist(self):
        """Verify behavior when no program with the given program_id in
        credentials exists.
        """
        self.create_programs_config()
        self.create_credentials_config()
        self.mock_programs_api()
        credential_data = [
            {
                "id": 1,
                "username": "test",
                "credential": {
                    "credential_id": 1,
                    "program_id": 100
                },
                "status": "awarded",
                "credential_url": "www.example.com"
            }
        ]
        actual = get_programs_for_credentials(self.user, credential_data)
        self.assertEqual(actual, [])
