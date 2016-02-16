"""
Middleware for Mobile APIs
"""
from datetime import datetime
from django.conf import settings
from django.http import HttpResponse
import re
from mobile_api.models import MobileAppVersionConfig
from openedx.core.lib.mobile_utils import is_request_from_mobile_app


class AppVersionUpgrade(object):
    """
    Middleware class to keep track of mobile application version being used
    """
    REGEX_USER_AGENT = {
        'android': (r'Dalvik/[.0-9]+ \(Linux; U; Android [.0-9]+; '
                    '(.*) Build/[0-9a-zA-Z]*\) (.*)/[0-9]+.[0-9]+.[0-9]+(.[0-9a-zA-Z]*)?'),
        'ios': r'\([0-9]+.[0-9]+.[0-9]+(.[0-9a-zA-Z]*)?; OS Version [0-9.]+ \(Build [0-9a-zA-Z]*\)\)',
    }

    def version_tuple(self, version):
        """ Converts string X.X.X to int tuple (X, X, X) """
        return tuple(map(int, (version.split("."))))

    def form_factor(self, user_agent):
        """ extracts mobile platform and app version in use """
        if re.search(self.REGEX_USER_AGENT['ios'], user_agent):
            # version is found betweet first occurrence ( and ; i.e. (version;
            user_app_version = user_agent[user_agent.find("(") + 1:user_agent.find(";")]
            return "ios", user_app_version
        elif re.search(self.REGEX_USER_AGENT['android'], user_agent):
            # version is found as last entry in android user agent after "/"
            user_app_version = user_agent[user_agent.rfind("/") + 1:]
            return "android", user_app_version

    def validate_version(self, user_app_version):
        """ if user app version confronts to X.X.X.Y format return X.X.X else None"""
        if re.match(settings.MOBILE_APP_VERSION_REGEX, user_app_version):
            if user_app_version.count(".") == 3:
                user_app_version = user_app_version[:user_app_version.rfind(".")]
            return user_app_version

    def process_request(self, request):
        """
        If request is from mobile native app and confront to X.X.X.Y version format (where X is a number and
        Y is optional alphanumeric), then return Http 426 Upgrade Required if;
        1. user app version < minimum supported version
        2. user app version >= minimum supported version and user app version < next supported version and
        request timestamp <= update required timespan for next supported version
        """
        if is_request_from_mobile_app(request):
            user_agent = request.META.get('HTTP_USER_AGENT')
            platform, user_app_version = self.form_factor(user_agent)

            # if user app version does not match to X.X.X.Y (acceptable format) then let pass the request
            # as it might belong to older apps
            user_app_version = self.validate_version(user_app_version)
            if user_app_version:
                user_app_version_tuple = self.version_tuple(user_app_version)
                app_version_config = MobileAppVersionConfig.current()

                min_supported_version = app_version_config.get_min_supported_version(platform)
                if user_app_version_tuple < self.version_tuple(min_supported_version):
                    return HttpResponse(status=426)

                next_supported_version = app_version_config.get_next_supported_version(platform)
                next_update_required = app_version_config.get_next_update_required(platform).replace(tzinfo=None)
                if user_app_version_tuple < self.version_tuple(next_supported_version):
                    if datetime.now() > next_update_required:
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
            platform, user_app_version = self.form_factor(user_agent)
            # if user app version does not match to X.X.X.Y (acceptable format) then do not add version info to
            # headers as this request might belong to older apps
            user_app_version = self.validate_version(user_app_version)
            if user_app_version:
                app_version_config = MobileAppVersionConfig.current()
                latest_version = app_version_config.get_latest_version(platform)
                user_app_version_tuple = self.version_tuple(user_app_version)
                if user_app_version_tuple < self.version_tuple(latest_version):
                    response["EDX-APP-LATEST-VERSION"] = latest_version
                next_supported_version = app_version_config.get_next_supported_version(platform)
                if user_app_version_tuple <= self.version_tuple(next_supported_version):
                    next_update_required = app_version_config.get_next_update_required(platform).replace(tzinfo=None)
                    response["EDX-APP-UPGRADE-DATE"] = next_update_required
        return response
