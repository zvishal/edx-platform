"""
This module defines SafeSessionMiddleware that makes use of a
SafeCookieData that cryptographically binds the user to the session id
in the cookie.

The implementation is inspired by the proposal in the following paper:
http://www.cse.msu.edu/~alexliu/publications/Cookie/cookie.pdf

Note: The proposed protocol protects against replay attacks by
incorporating the session key used in the SSL connection.  However,
this does not suit our needs since we want the ability to reuse the
same cookie over multiple SSL connections.  So instead, we mitigate
replay attacks by enforcing session cookie expiration
(via TimestampSigner) and assuming SESSION_COOKIE_SECURE (see below).

We use django's built-in Signer class, which makes use of a built-in
salted_hmac function that derives a usage-specific key from the
server's SECRET_KEY, as proposed in the paper.

Note: The paper proposes deriving a usage-specific key from the
session's expiration time in order to protect against volume attacks.
However, since django does not always use an expiration time, we
instead use a random key salt to prevent volume attacks.

In fact, we actually use a specialized subclass of Signer called
TimestampSigner. This signer binds a timestamp along with the signed
data and verifies that the signature has not expired.  We do this
since django's session stores do not actually verify the expiration
of the session cookies.  Django instead relies on the browser to honor
session cookie expiration.

The resulting safe cookie data that gets stored as the value in the
session cookie is a tuple of:
    (
        version,
        session_id,
        key_salt,
        signature
    )

    where signature is:
        signed_data : base64(HMAC_SHA1(signed_data, usage_key))

    where signed_data is:
        H(version | session_id | user_id) : timestamp

    where usage_key is:
        SHA1(key_salt + 'signer' + settings.SECRET_KEY)

Note: We assume that the SESSION_COOKIE_SECURE setting is set to
TRUE to prevent inadvertent leakage of the session cookie to a
person-in-the-middle.  The SESSION_COOKIE_SECURE flag indicates
to the browser that the cookie should be sent only over an
SSL-protected channel.  Otherwise, a session hijacker could copy
the entire cookie and use it to impersonate the victim.

"""

from django.conf import settings
from django.contrib.auth import SESSION_KEY
from django.contrib.auth.views import redirect_to_login
from django.contrib.sessions.middleware import SessionMiddleware
from django.core import signing
from django.utils.crypto import get_random_string
from hashlib import sha256
from logging import getLogger
import json

from student.views import logout_user


log = getLogger(__name__)


class SafeCookieError(Exception):
    """
    An exception class for safe cookie related errors.
    """
    def __init__(self, error_message):
        super(SafeCookieError, self).__init__(error_message)
        log.error(error_message)


class SafeCookieData(object):
    """
    Cookie data that cryptographically binds and timestamps the user
    to the session id.  It verifies the freshness of the cookie by
    checking its creation date using settings.SESSION_COOKIE_AGE.
    """
    CURRENT_VERSION = 1

    def __init__(self, version, session_id, key_salt, signature):
        """
        Arguments:
            version (int): The data model version of the safe cookie
                data that is checked for forward and backward
                compatibility.
            session_id (string): Unique and unguessable session
                identifier to which this safe cookie data is bound.
            key_salt (string): A securely generated random string that
                is used to derive a usage-specific secret key for
                signing the safe cookie data to protect against volume
                attacks.
            signature (string): Cryptographically created signature
                for the safe cookie data that binds the session_id
                and its corresponding user as described at the top of
                this file.
        """
        self.version = version
        self.session_id = session_id
        self.key_salt = key_salt
        self.signature = signature

    @classmethod
    def create(cls, session_id, user_id):
        """
        Factory method for creating the cryptographically bound
        safe cookie data for the session and the user.

        Raises SafeCookieError if session_id or user_id are None.
        """
        if not session_id or session_id == unicode(None):
            # The session ID should always be valid in the cookie.
            raise SafeCookieError(
                "SafeCookieData not created due to invalid value for session_id '{}' for user_id '{}'.".format(
                    session_id,
                    user_id,
                ))
        if not user_id:
            # The user ID is sometimes not set for
            # 3rd party Auth and external Auth transactions
            # as some of the session requests are made as
            # Anonymous users.
            log.warning(
                "SafeCookieData received empty user_id '%s' for session_id '%s'.",
                user_id,
                session_id,
            )
        safe_cookie_data = SafeCookieData(
            cls.CURRENT_VERSION,
            session_id,
            key_salt=get_random_string(),
            signature=None,
        )
        safe_cookie_data.sign(user_id)
        return safe_cookie_data

    @classmethod
    def parse(cls, safe_cookie_string):
        """
        Factory method that parses the serialized safe cookie data,
        verifies the version, and returns the safe cookie object.

        Raises SafeCookieError if there are any issues parsing the
        safe_cookie_string.
        """
        try:
            safe_cookie_data = SafeCookieData(*json.loads(safe_cookie_string))
        except ValueError:
            raise SafeCookieError("SafeCookieData could not be parsed as JSON '{0!r}'.".format(safe_cookie_string))
        except TypeError:
            raise SafeCookieError(
                "SafeCookieData not instantiated due to number of arguments '{0!r}'.".format(safe_cookie_string)
            )
        else:
            if safe_cookie_data.version != cls.CURRENT_VERSION:
                raise SafeCookieError(
                    "SafeCookieData version '{0!r}' is not supported. Current version is '{1}'.".format(
                        safe_cookie_data.version,
                        cls.CURRENT_VERSION,
                    ))
            return safe_cookie_data

    def __unicode__(self):
        """
        Returns a string serialization of the safe cookie data.
        """
        return json.dumps((self.version, self.session_id, self.key_salt, self.signature))

    def sign(self, user_id):
        """
        Computes the signature of this safe cookie data.
        A signed value of hash(version | session_id | user_id):timestamp
        with a usage-specific key derived from key_salt.
        """
        data_to_sign = self._compute_digest(user_id)
        self.signature = signing.dumps(data_to_sign, salt=self.key_salt)

    def verify(self, user_id):
        """
        Verifies the signature of this safe cookie data.
        Successful verification implies this cookie data is fresh
        (not expired) and bound to the given user.

        Raises SafeCookieError if there are any verification issues.
        """
        try:
            unsigned_data = signing.loads(self.signature, salt=self.key_salt, max_age=settings.SESSION_COOKIE_AGE)
            if unsigned_data != self._compute_digest(user_id):
                raise SafeCookieError("SafeCookieData '{0!r}' is not bound to user '{1}'.".format(unicode(self), user_id))
        except signing.BadSignature as sig_error:
            raise SafeCookieError(
                "SafeCookieData signature error for cookie data '{0!r}': {1}".format(unicode(self), sig_error.message)
            )

    def _compute_digest(self, user_id):
        """
        Returns hash(version | session_id | user_id |)
        """
        hash_func = sha256()
        for data_item in [self.version, self.session_id, user_id]:
            hash_func.update(unicode(data_item))
            hash_func.update('|')
        return hash_func.hexdigest()


class SafeSessionMiddleware(SessionMiddleware):
    """
    A safer middleware implementation that uses SafeCookieData instead
    of just the session id to lookup and verify a user's session.
    """
    def process_request(self, request):
        """
        Processing the request is a multi-step process, as follows:

        Step 1. The safe_cookie_data is parsed and verified from the
        session cookie.

        Step 2. The session_id is retrieved from the safe_cookie_data
        and stored in place of the session cookie value, to be used by
        Django's Session middleware.

        Step 3. Call Django's Session Middleware to find the session
        corresponding to the session_id and to set the session in the
        request.

        Step 4. Once the session is retrieved, verify that the user
        bound in the safe_cookie_data matches the user attached to the
        server's session information.

        Step 5. If all is successful, the now verified user_id is stored
        separately in the request object so it is available for another
        final verification before sending the response (in
        process_response).
        """
        should_logout_user = False

        try:

            cookie_data_string = request.COOKIES.get(settings.SESSION_COOKIE_NAME)
            if cookie_data_string:

                # Step 1. Parse the safe cookie data.
                safe_cookie_data = SafeCookieData.parse(cookie_data_string)

                # Step 2. Replace the cookie value in the request with
                # the bare session_id for use by Django's
                # SessionMiddleware (in the super call to the parent
                # class).
                request.COOKIES[settings.SESSION_COOKIE_NAME] = safe_cookie_data.session_id

        except SafeCookieError:
            # For security reasons, we don't support requests with
            # older or invalid session cookie models.
            should_logout_user = True

        # Step 3. Call the super class to find/set the session for the
        # request.
        process_request_response = super(SafeSessionMiddleware, self).process_request(request)
        if process_request_response:
            # The process_request pipeline has been short circuited so
            # return the response.
            return process_request_response

        if (cookie_data_string and request.session.get(SESSION_KEY)):
            try:
                # Step 4. Verify that the user found in the session
                # corresponds to the user bound to the cookie data.
                user_id = request.session[SESSION_KEY]
                safe_cookie_data.verify(user_id)

                # Step 5. Store the verified user_id in the request
                # object for another final verification before sending
                # response in SafeSessionMiddleware.process_response.
                request.safe_cookie_verified_user_id = user_id

            except SafeCookieError:
                should_logout_user = True

        if should_logout_user:
            # Note: The logout_user method assumes the session is
            # stored in the request object so call it only after
            # the super class's process_request was successful.
            return logout_user(request)

    def process_response(self, request, response):
        """
        When creating a cookie for the response, a safe_cookie_data
        is created and put in place of the session_id in the session
        cookie.

        Also, the session cookie is deleted if prior verification failed
        or the designated user in the request has changed since the
        original request.

        Processing the response is a multi-step process, as follows:

        Step 1. Call the parent's method to generate the basic cookie.

        Step 2. Check whether the cookie was previously marked for
        deletion due to previous verification errors.

        Step 3. Verify that the user marked at the time of
        process_request matches the user at this time when processing
        the response.  If not, mark the cookie for deletion.

        Step 4. If a cookie is being sent with the response, update
        the cookie by replacing its session_id with a safe_cookie_data
        that binds the session and its corresponding user.

        Step 5. Delete the cookie, if it's marked for deletion.

        """

        # Step 1. Call the parent class's process_response to generate
        # the basic cookie for the response.
        response = super(SafeSessionMiddleware, self).process_response(request, response)

        # Check whether a cookie is present
        if (
                response.cookies.get(settings.SESSION_COOKIE_NAME) and  # cookie in response
                response.cookies[settings.SESSION_COOKIE_NAME].value  # cookie is not empty
        ):
            try:
                # Step 2. Verify user designated at request time
                # matches the user at this response time.
                if (
                        hasattr(request, 'safe_cookie_verified_user_id') and
                        request.safe_cookie_verified_user_id != request.user.id
                ):
                    # Theoretically, this should not happen.
                    # However, there may be an implementation issue
                    # that overrides the user in the request object.
                    # So we catch it and fail by deleting the
                    # cookie.
                    raise SafeCookieError(
                        "SafeCookieData user at request '{}' does not match user at response: '{}'".format(
                            request.safe_cookie_verified_user_id,
                            request.user.id,
                        ))

                # Step 3. Since a cookie is being sent, update the
                # cookie by replacing the session_id with a freshly
                # computed safe_cookie_data.
                self.update_with_safe_session_cookie(response.cookies, request.user.id)

            except SafeCookieError:
                # There was an error creating the safe_cookie_data
                # so delete the existing cookie.
                #
                # Delete the cookie by setting the expiration to a date in
                # the past, while maintaining the domain, secure, and
                # httponly settings.
                response.set_cookie(
                    settings.SESSION_COOKIE_NAME,
                    max_age=0,
                    expires='Thu, 01-Jan-1970 00:00:00 GMT',
                    domain=settings.SESSION_COOKIE_DOMAIN,
                    secure=settings.SESSION_COOKIE_SECURE or None,
                    httponly=settings.SESSION_COOKIE_HTTPONLY or None,
                )

        # Return the updated response with the updated cookie, if
        # applicable.
        return response

    @classmethod
    def update_with_safe_session_cookie(cls, cookies, user_id):
        """
        Replaces the session_id in the session cookie with a freshly
        computed safe_cookie_data.
        """
        # Create safe cookie data that binds the user with the session
        # in place of just storing the session_key in the cookie.
        safe_cookie_data = SafeCookieData.create(
            cookies[settings.SESSION_COOKIE_NAME].value,
            user_id,
        )

        # Update the cookie's value with the safe_cookie_data.
        cookies[settings.SESSION_COOKIE_NAME] = unicode(safe_cookie_data)
