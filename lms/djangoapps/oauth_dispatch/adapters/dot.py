"""
Adapter to isolate django-oauth-toolkit dependencies
"""

from oauth2_provider import models


class DOTAdapter(object):
    """
    Standard interface for working with django-oauth-toolkit
    """

    backend = object()

    def create_confidential_client(self, user, client_id=None):
        return models.Application.objects.create(
            name='Test Auth Code Application',
            client_type=models.Application.CLIENT_CONFIDENTIAL,
            client_id=client_id,
            authorization_grant_type=models.Application.GRANT_AUTHORIZATION_CODE,
            user=user,
            redirect_uris='http://example.edx/redirect',
        )

    def create_public_client(self, user, client_id=None):
        return models.Application.objects.create(
            name='Test Password Application',
            client_id=client_id,
            client_type=models.Application.CLIENT_PUBLIC,
            authorization_grant_type=models.Application.GRANT_PASSWORD,
            redirect_uris='http://example.edx/redirect',
            user=user,
        )

    def get_client(self, **filters):
        return models.Application.objects.get(**filters)

    def get_client_for_token(self, token):
        return token.application

    def get_access_token(self, token_string):
        return models.AccessToken.objects.get(token=token_string)

    def get_token_response_keys(self):
        return {'access_token', 'token_type', 'expires_in', 'scope', 'refresh_token'}

    def normalize_scopes(self, scopes):
        if not scopes:
            scopes = ['default']
        return ' '.join(scopes)

    def get_token_scope_names(self, token):
        return list(token.scopes)
