"""
ConfigurationModel for the mobile_api djangoapp.
"""

from django.db.models.fields import TextField, DateTimeField

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
    latest_version_android = TextField(
        blank=False,
        help_text="Latest available version for android app in X.X.X format"
    )
    latest_version_ios = TextField(
        blank=False,
        help_text="Latest available version for IOS app in X.X.X format"
    )
    min_supported_version_android = TextField(
        blank=False,
        help_text="Min supported version for android app in X.X.X format"
    )
    min_supported_version_ios = TextField(
        blank=False,
        help_text="Min supported version for IOS app in X.X.X format"
    )
    next_supported_version_android = TextField(
        blank=False,
        help_text="Next supported version for android app in X.X.X format that a user must upgrade to before deadline"
    )
    next_supported_version_ios = TextField(
        blank=False,
        help_text="Next supported version for IOS app in X.X.X format that a user must upgrade to before deadline"
    )
    next_update_required_android = DateTimeField(
        verbose_name="Upgrade Deadline"
    )
    next_update_required_ios = DateTimeField(
        verbose_name="Upgrade Deadline"
    )

    def get_next_supported_version(self, platform):
        """ get next supported version that has a deadline to upgrade """
        return {
            'android': self.next_supported_version_android,
            'ios': self.next_supported_version_ios,
        }.get(platform, None)

    def get_next_update_required(self, platform):
        """ get next update required date corresponding to next supported version """
        return {
            'android': self.next_update_required_android,
            'ios': self.next_update_required_ios,
        }.get(platform, None)

    def get_min_supported_version(self, platform):
        """ get minimum supported app version """
        return {
            'android': self.min_supported_version_android,
            'ios': self.min_supported_version_ios,
        }.get(platform, None)

    def get_latest_version(self, platform):
        """ get latest version available """
        return {
            'android': self.latest_version_android,
            'ios': self.latest_version_ios,
        }.get(platform, None)
