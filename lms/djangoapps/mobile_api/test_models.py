"""
tests for version based app upgrade configuration model
"""
from datetime import datetime
import ddt
from django.test import TestCase
import pytz
from mobile_api.models import MobileAppVersionConfig


@ddt.ddt
class TestMobileAppVersionConfig(TestCase):
    """ Tests for version based app upgrade model"""
    def setUp(self):
        super(TestMobileAppVersionConfig, self).setUp()
        update_deadline = datetime(2016, 02, 22, tzinfo=pytz.utc)
        MobileAppVersionConfig(
            platform="android",
            latest_version="5.5.5",
            min_supported_version="2.0.2",
            next_min_supported_version="3.2.1",
            update_required_date=update_deadline,
        ).save()
        MobileAppVersionConfig(
            platform="ios",
            latest_version="5.5.5",
            min_supported_version="2.0.2",
            next_min_supported_version="3.2.1",
            update_required_date=update_deadline,
        ).save()
        self.android_app_version_config = MobileAppVersionConfig.current("android")
        self.ios_app_version_config = MobileAppVersionConfig.current("ios")

    @ddt.data(
        ("1.0.1", True),
        ("2.5.2", True),
        ("4.4.0", False),
        ("5.5.5", False),
    )
    @ddt.unpack
    def test_is_outdated_version(self, user_app_version, result):
        self.assertEqual(result, self.android_app_version_config.is_outdated_version(user_app_version))
        self.assertEqual(result, self.ios_app_version_config.is_outdated_version(user_app_version))

    @ddt.data(
        ("4.0.1", True),
        ("5.5.5", False),
    )
    @ddt.unpack
    def test_is_new_version_available(self, user_app_version, result):
        self.assertEqual(result, self.android_app_version_config.is_new_version_available(user_app_version))
        self.assertEqual(result, self.ios_app_version_config.is_new_version_available(user_app_version))

    @ddt.data(
        ("2.0.1", True),
        ("3.2.1", True),
        ("4.1.0", False),
        ("5.5.5", False),
    )
    @ddt.unpack
    def test_is_deprecated_version(self, user_app_version, result):
        self.assertEqual(result, self.android_app_version_config.is_deprecated_version(user_app_version))
        self.assertEqual(result, self.ios_app_version_config.is_deprecated_version(user_app_version))
