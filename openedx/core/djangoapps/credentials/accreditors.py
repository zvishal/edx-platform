from __future__ import unicode_literals
from itertools import groupby

from openedx.core.djangoapps.credentials.issuers import CourseCertificateIssuer


class Accreditor(object):
    def __init__(self, issuers=None):
        if not issuers:
            issuers = [CourseCertificateIssuer()]

        self.issuers = issuers
        self._create_credential_type_issuer_map()

    def _create_credential_type_issuer_map(self):
        """Creates a map from credential type slug to a list of credential issuers."""

        def keyfunc(issuer):
            return issuer.issued_credential_type.credential_type_slug

        self.issuers = sorted(self.issuers, key=keyfunc)
        self.credential_type_issuer_map = {}
        for credential_type, group in groupby(self.issuers, key=keyfunc):
            self.credential_type_issuer_map[credential_type] = list(group)

    def issue_credential(self, credential_type, username, **kwargs):
        """Issues a credential.

        Arguments:
            credential_type (string): Type of credential to be issued.
            username (string): Username of the recipient.
            **kwargs: Arbitrary keyword arguments passed to the issuer class.

        Returns:
            UserCredential

        Raises:
            UnsupportedCredentialTypeError: If the specified credential type is not supported (cannot be issued).
        """
        raise NotImplemented
