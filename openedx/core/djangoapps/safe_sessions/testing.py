"""
Test overrides to support Safe Cookies with Test Clients.
"""

from django.conf import settings
from django.contrib.auth import SESSION_KEY
from django.test.client import Client
from django.utils.importlib import import_module

from .middleware import SafeSessionMiddleware, SafeCookieData, SafeCookieError


def safe_cookie_test_session_patch():
    """
    Override the Test Client's methods in order to support Safe Cookies.
    If there's a better way to patch this, we should do so.
    """
    if getattr(safe_cookie_test_session_patch, 'has_run', False):
        return

    using_safe_cookie_data = (
        'openedx.core.djangoapps.safe_sessions.middleware.SafeSessionMiddleware' in settings.MIDDLEWARE_CLASSES
    )

    # Don't bother patching the Test Client unless we are
    # actually using Safe Cookies.
    if using_safe_cookie_data:

        #--- session_id ---> safe_cookie_data ---#

        # Override Client.login method to update cookies with safe
        # cookies.
        patched_client_login = Client.login

        def login_with_safe_session(self, **credentials):
            """
            Call the original Client.login method, but update the
            session cookie with a freshly computed safe_cookie_data
            before returning.
            """
            if not patched_client_login(self, **credentials):
                return False
            SafeSessionMiddleware.update_with_safe_session_cookie(self.cookies, self.session[SESSION_KEY])
            return True
        Client.login = login_with_safe_session

        #--- safe_cookie_data ---> session_id ---#

        # Override Client.session so any safe cookies are parsed before
        # use.
        def get_safe_session(self):
            """
            Here, we are duplicating the original Client._session code
            in order to allow conversion of the safe_cookie_data back
            to the raw session_id, if needed.  Since test code may
            access the session_id before it's actually converted,
            we use a try-except clause here to check both cases.
            """
            engine = import_module(settings.SESSION_ENGINE)
            cookie = self.cookies.get(settings.SESSION_COOKIE_NAME, None)
            if cookie:
                session_id = cookie.value
                if using_safe_cookie_data:
                    try:
                        session_id = SafeCookieData.parse(session_id).session_id
                    except SafeCookieError:
                        pass  # The safe cookie hasn't yet been created.
                return engine.SessionStore(session_id)
            return {}
        Client.session = property(get_safe_session)

    safe_cookie_test_session_patch.has_run = True
