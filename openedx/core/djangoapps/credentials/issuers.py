from __future__ import unicode_literals

import abc

from openedx.core.djangoapps.credentials.models import CourseCertificate, ProgramCertificate


class AbstractCredentialIssuer(object):
    """
    Abstract credential issuer.

    Credential issuers are responsible for taking inputs and issuing a single credential (subclass of
    ``AbstractCredential``) to a given user.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def issued_credential_type(self):
        """
        Type of credential issued by

        Returns:
            AbstractCredential
        """
        pass

    @abc.abstractmethod
    def issue_credential(self, username, **kwargs):
        """
        Issue a credential to the user.

        This action is idempotent. If the user has already earned the credential, a new one WILL NOT be issued. The
        existing credential WILL NOT be modified.

        Arguments:
            username (string): Username of the credential recipient.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            ``UserCredential``
        """
        pass


class CourseCertificateIssuer(AbstractCredentialIssuer):
    issued_credential_type = CourseCertificate

    def issue_credential(self, username, **kwargs):
        raise NotImplemented


class ProgramCertificateIssuer(AbstractCredentialIssuer):
    issued_credential_type = ProgramCertificate

    def issue_credential(self, username, **kwargs):
        raise NotImplemented
