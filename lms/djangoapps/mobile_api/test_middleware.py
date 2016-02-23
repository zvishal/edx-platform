"""
tests for version based app upgrade middleware
"""
from datetime import datetime
import ddt
from django.http import HttpRequest, HttpResponse
from django.test import TestCase
import pytz
from mobile_api.middleware import AppVersionUpgrade
from mobile_api.models import MobileAppVersionConfig


@ddt.ddt
class TestAppVersionUpgradeMiddleware(TestCase):
    """ Tests for version based app upgrade middleware"""
    def setUp(self):
        super(TestAppVersionUpgradeMiddleware, self).setUp()
        self.middleware = AppVersionUpgrade()
        update_deadline = datetime(2016, 02, 22, tzinfo=pytz.utc)
        MobileAppVersionConfig(
            platform="ios",
            latest_version="5.5.5",
            min_supported_version="2.0.2",
            next_min_supported_version="3.2.1",
            update_required_date=update_deadline,
        ).save()
        MobileAppVersionConfig(
            platform="android",
            latest_version="5.5.5",
            min_supported_version="2.0.2",
            next_min_supported_version="3.2.1",
            update_required_date=update_deadline,
        ).save()

    @ddt.data(
        ("Mozilla/5.0 (Linux; Android 5.1; Nexus 5 Build/LMY47I; wv) AppleWebKit/537.36 (KHTML, like Gecko) "
         "Version/4.0 Chrome/47.0.2526.100 Mobile Safari/537.36 edX/org.edx.mobile/2.0.0"),
        ("Mozilla/5.0 (iPhone; CPU iPhone OS 9_2 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) "
         "Mobile/13C75 edX/org.edx.mobile/2.2.1"),
        ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 "
         "Safari/537.36"),
    )
    def test_non_mobile_app_requests(self, user_agent):
        """ request that are not from mobile native apps """
        fake_request = HttpRequest()
        fake_request.META['HTTP_USER_AGENT'] = user_agent
        self.assertIsNone(self.middleware.process_request(fake_request))
        fake_response = HttpResponse()
        response = self.middleware.process_response(fake_request, fake_response)
        self.assertEquals(200, response.status_code)
        with self.assertRaises(KeyError):
            response[AppVersionUpgrade.LATEST_VERSION]
        with self.assertRaises(KeyError):
            response[AppVersionUpgrade.UPGRADE_DEADLINE]

    @ddt.data(
        "edX/org.edx.mobile (5.5.5; OS Version 9.2 (Build 13C75))",
        "Dalvik/2.1.0 (Linux; U; Android 5.1; Nexus 5 Build/LMY47I) edX/org.edx.mobile/5.5.5",
    )
    def test_no_update(self, user_agent):
        """ user has the latest app version """
        fake_request = HttpRequest()
        fake_request.META['HTTP_USER_AGENT'] = user_agent
        self.assertIsNone(self.middleware.process_request(fake_request))
        fake_response = HttpResponse()
        response = self.middleware.process_response(fake_request, fake_response)
        self.assertEquals(200, response.status_code)
        with self.assertRaises(KeyError):
            response[AppVersionUpgrade.LATEST_VERSION]
        with self.assertRaises(KeyError):
            response[AppVersionUpgrade.UPGRADE_DEADLINE]

    @ddt.data(
        "edX/org.edx.mobile (1.0.0; OS Version 9.2 (Build 13C75))",
        "edX/org.edx.mobile (2.2.1; OS Version 9.2 (Build 13C75))",
        "edX/org.edx.mobile (2.2.1.RC; OS Version 9.2 (Build 13C75))",
        "Dalvik/2.1.0 (Linux; U; Android 5.1; Nexus 5 Build/LMY47I) edX/org.edx.mobile/1.0.0",
        "Dalvik/2.1.0 (Linux; U; Android 5.1; Nexus 5 Build/LMY47I) edX/org.edx.mobile/2.2.1",
        "Dalvik/2.1.0 (Linux; U; Android 5.1; Nexus 5 Build/LMY47I) edX/org.edx.mobile/2.2.1.RC",
    )
    def test_upgrade_required(self, user_agent):
        """ when;
        1. user version < min supported version
        2. user version >= min supported version and user version < next min supported version
        and request timestamp <= update required timestamp
        """
        fake_request = HttpRequest()
        fake_request.META['HTTP_USER_AGENT'] = user_agent
        result = self.middleware.process_request(fake_request)
        self.assertIsNotNone(result)
        response = self.middleware.process_response(fake_request, result)
        self.assertEquals(426, response.status_code)
        self.assertEqual("5.5.5", response[AppVersionUpgrade.LATEST_VERSION])
        self.assertEqual('2016-02-22 00:00:00+00:00', response[AppVersionUpgrade.UPGRADE_DEADLINE])

    @ddt.data(
        "edX/org.edx.mobile (4.1.1; OS Version 9.2 (Build 13C75))",
        "edX/org.edx.mobile (4.2.2.RC; OS Version 9.2 (Build 13C75))",
        "Dalvik/2.1.0 (Linux; U; Android 5.1; Nexus 5 Build/LMY47I) edX/org.edx.mobile/4.1.1",
        "Dalvik/2.1.0 (Linux; U; Android 5.1; Nexus 5 Build/LMY47I) edX/org.edx.mobile/4.2.2.RC",
    )
    def test_new_update_available(self, user_agent):
        """ user version > next min supported version and user version < latest version """
        fake_request = HttpRequest()
        fake_request.META['HTTP_USER_AGENT'] = user_agent
        self.assertIsNone(self.middleware.process_request(fake_request))
        fake_response = HttpResponse()
        response = self.middleware.process_response(fake_request, fake_response)
        self.assertEquals(200, response.status_code)
        self.assertEqual("5.5.5", response[AppVersionUpgrade.LATEST_VERSION])
        with self.assertRaises(KeyError):
            response[AppVersionUpgrade.UPGRADE_DEADLINE]
