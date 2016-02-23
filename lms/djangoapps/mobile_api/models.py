"""
ConfigurationModel for the mobile_api djangoapp.
"""
from datetime import datetime

from django.db.models.fields import TextField, DateTimeField, CharField

from config_models.models import ConfigurationModel


class MobileApiConfig(ConfigurationModel):
    """
    Configuration for the video upload feature.

    The order in which the comma-separated list of names of profiles are given
    is in priority order.
    """
    video_profiles = TextField(
        blank=True,
        help_text="A comma-separated list of names of profiles to include for videos returned from the mobile API."
    )

    @classmethod
    def get_video_profiles(cls):
        """
        Get the list of profiles in priority order when requesting from VAL
        """
        return [profile.strip() for profile in cls.current().video_profiles.split(",") if profile]


class MobileAppVersionConfig(ConfigurationModel):  # pylint: disable=model-missing-unicode
    """
    Configuration for mobile app versions available.
    """
    IOS = "ios"
    ANDROID = "android"
    MOBILE_PLATFORM = (
        (IOS, "IOS"),
        (ANDROID, "ANDROID"),

    )
    KEY_FIELDS = ('platform', )  # mobile platform is unique
    platform = CharField(
        max_length=50,
        choices=MOBILE_PLATFORM,
        blank=False,
        help_text="mobile device platform")
    latest_version = TextField(blank=False, help_text="Latest available version for app in X.X.X format")
    min_supported_version = TextField(blank=False, help_text="Min supported version for app in X.X.X format")
    next_min_supported_version = TextField(
        blank=False,
        help_text="Next supported version for app in X.X.X format that a user must upgrade to before deadline"
    )
    update_required_date = DateTimeField(verbose_name="Upgrade Deadline")

    def parsed_version(self, version):
        """ Converts string X.X.X.Y to tuple (X, X, X, Y) and return (X, X, X) """
        return tuple(version.split("."))[:3]

    def is_outdated_version(self, user_app_version):
        """
        This is the case if user app version is no longer supported. Return True if
        1. user app version is less than minimum supported version
        2. user app version >= minimum supported version and user app version < next minimum supported version and
        request timestamp > upgrade deadline
        """
        user_app_version = self.parsed_version(user_app_version)
        if (user_app_version < self.parsed_version(self.min_supported_version) or (
                user_app_version < self.parsed_version(self.next_min_supported_version) and
                datetime.now() > self.update_required_date.replace(tzinfo=None)
        )):
            return True
        else:
            return False

    def is_new_version_available(self, user_app_version):
        """ True if user is using older version of app """
        return True if self.parsed_version(user_app_version) < self.parsed_version(self.latest_version) else False

    def is_deprecated_version(self, user_app_version):
        """
        This is the case when there exists a higher version (than user app user) that would contain critical/major
        application changes and would be bound with a deadline to upgrade.
        """
        if self.parsed_version(user_app_version) <= self.parsed_version(self.next_min_supported_version):
            return True
        else:
            return False
