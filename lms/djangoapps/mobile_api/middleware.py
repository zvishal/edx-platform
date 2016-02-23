"""
Middleware for Mobile APIs
"""
from django.conf import settings
from django.http import HttpResponse
import re
from mobile_api.models import MobileAppVersionConfig
from openedx.core.lib.mobile_utils import is_request_from_mobile_app


class AppVersionUpgrade(object):
    """
    Middleware class to keep track of mobile application version being used
    """
    LATEST_VERSION = "EDX-APP-LATEST-VERSION"
    UPGRADE_DEADLINE = "EDX-APP-UPGRADE-DATE"
    MOBILE_PLATFORM_USER_AGENT_REGEX = {
        MobileAppVersionConfig.ANDROID: (r'Dalvik/[.0-9]+ \(Linux; U; Android [.0-9]+; '
                                         r'(.*) Build/[0-9a-zA-Z]*\) (.*)/[0-9]+.[0-9]+.[0-9]+(.[0-9a-zA-Z]*)?'),
        MobileAppVersionConfig.IOS: (r'\([0-9]+.[0-9]+.[0-9]+(.[0-9a-zA-Z]*)?; '
                                     r'OS Version [0-9.]+ \(Build [0-9a-zA-Z]*\)\)'),
    }
    MOBILE_PLATFORM_VERSION = {
        # version is found as last entry in android user agent after "/"
        MobileAppVersionConfig.ANDROID: lambda user_agent: user_agent[user_agent.rfind("/") + 1:],
        # version is found between first occurrence ( and ; i.e. (version;
        MobileAppVersionConfig.IOS: lambda user_agent: user_agent[user_agent.find("(") + 1:user_agent.find(";")],
    }

    def form_factor(self, user_agent):
        """ extracts mobile platform and app version in use """
        form_factor = None
        for platform, user_agent_regex in self.MOBILE_PLATFORM_USER_AGENT_REGEX.iteritems():
            if re.search(user_agent_regex, user_agent):
                user_app_version = self.MOBILE_PLATFORM_VERSION[platform](user_agent)
                # if user app version does not match to X.X.X.Y (acceptable format) then let pass the request
                # as it might belong to older apps, so return None
                if self.validate_version(user_app_version):
                    return {"platform": platform, "user_app_version": user_app_version}
                break
        return form_factor

    def validate_version(self, user_app_version):
        """ if user app version confronts to X.X.X.Y format return X.X.X else None"""
        if re.match(settings.MOBILE_APP_VERSION_REGEX, user_app_version):
            return True

    def process_request(self, request):
        """
        If request is from mobile native app and confront to X.X.X.Y version format (where X is a number and
        Y is optional alphanumeric), and return Http 426 if version upgrade is required; else let pass the request
        """
        if is_request_from_mobile_app(request):
            user_agent = request.META.get('HTTP_USER_AGENT')
            form_factor = self.form_factor(user_agent)
            if form_factor:
                app_version_config = MobileAppVersionConfig.current(form_factor["platform"])
                if app_version_config.is_outdated_version(form_factor["user_app_version"]):
                    return HttpResponse(status=426)

    def process_response(self, _request, response):
        """
        If request is from mobile native app and confront to X.X.X.Y version format (where X is a number and
        Y is optional alphanumeric), then add headers to response;
        1. EDX-APP-LATEST-VERSION; if user app version < latest available version
        2. EDX-APP-UPGRADE-DATE; if user app version < next supported version
        """
        if is_request_from_mobile_app(_request):
            user_agent = _request.META.get('HTTP_USER_AGENT')
            form_factor = self.form_factor(user_agent)
            if form_factor:
                user_app_version = form_factor["user_app_version"]
                app_version_config = MobileAppVersionConfig.current(form_factor["platform"])
                if app_version_config.is_new_version_available(user_app_version):
                    response[self.LATEST_VERSION] = app_version_config.latest_version
                if app_version_config.is_deprecated_version(user_app_version):
                    response[self.UPGRADE_DEADLINE] = app_version_config.update_required_date
        return response
