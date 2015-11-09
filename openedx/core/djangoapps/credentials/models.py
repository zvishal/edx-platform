from __future__ import unicode_literals

import abc
from django.contrib.contenttypes.generic import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext as _
from model_utils.models import TimeStampedModel

STATUS_CHOICES = (
    (_('Awarded'), 'awarded'),
    (_('Pending'), 'pending'),
    (_('Revoked'), 'revoked'),
)

MODE_CHOICES = (
    (_('Honor'), 'honor'),
    (_('Verified'), 'verified'),
    (_('Professional'), 'professional'),
)


class AbstractCredential(TimeStampedModel):
    site = models.ForeignKey('sites.Site')

    @abc.abstractproperty
    def credential_type_slug(self):
        """
        Slug representing the type of this credential

        Returns:
            string
        """
        pass

    class Meta(object):
        abstract = True


class Signatory(TimeStampedModel):
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    # TODO Upload to S3
    image = models.ImageField()


class TemplateAsset(TimeStampedModel):
    name = models.CharField(max_length=255)
    file = models.FileField()


# TODO Determine how to handle custom assets (reference TemplateAsset via name)
# TODO Limit edit access to "Credential Template Administrators" group
class CertificateTemplate(TimeStampedModel):
    name = models.CharField(max_length=255)
    content = models.TextField()


class AbstractCertificate(AbstractCredential):
    signatories = models.ManyToManyField(Signatory)
    template = models.ForeignKey(CertificateTemplate)

    class Meta(object):
        abstract = True


class CourseCertificate(AbstractCertificate):
    credential_type_slug = 'course-certificate'

    # TODO Add regex validation
    course_id = models.CharField(max_length=255)
    mode = models.CharField(max_length=255, choices=MODE_CHOICES)

    class Meta(object):
        unique_together = (('course_id', 'mode'),)


class ProgramCertificate(AbstractCertificate):
    credential_type_slug = 'program-certificate'

    program_id = models.IntegerField()

    class Meta(object):
        unique_together = (('program_id', 'mode'),)


class UserCredential(TimeStampedModel):
    credential_content_type = models.ForeignKey(ContentType)
    credential_id = models.PositiveIntegerField()
    credential = GenericForeignKey('credential_content_type', 'credential_id')
    # TODO Use custom user model for service
    user = models.ForeignKey('auth.User', null=False, blank=False)
    status = models.CharField(max_length=255, choices=STATUS_CHOICES)
    uuid = models.CharField(max_length=255, null=False, blank=False)

    class Meta(object):
        unique_together = (('user', 'credential'),)
        # TODO Determine if/how to index for a given credential (to answer
        # the question of how many users have received a given credential).


class UserCredentialNotes(TimeStampedModel):
    user_credential = models.ForeignKey(UserCredential, related_name='notes')
    note = models.TextField()
