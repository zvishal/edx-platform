"""
Adapter to isolate django-oauth-toolkit dependencies
"""

from provider.oauth2 import models
from provider import constants, scope


class DOPAdapter(object):
    """
    Standard interface for working with django-oauth-toolkit
    """

    backend = object()

    def create_confidential_client(self, user, client_id=None):
        return models.Client.objects.create(
            user=user,
            client_id=client_id,
            redirect_uri='http://example.edx/redirect',
            client_type=constants.CONFIDENTIAL,
        )

    def create_public_client(self, user, client_id=None):
        return models.Client.objects.create(
            user=user,
            client_id=client_id,
            redirect_uri='http://example.edx/redirect',
            client_type=constants.PUBLIC
        )

    def get_client(self, **filters):
        return models.Client.objects.get(**filters)

    def get_client_for_token(self, token):
        return token.client

    def get_access_token(self, token_string):
        return models.AccessToken.objects.get(token=token_string)

    def get_token_response_keys(self):
        return {'access_token', 'token_type', 'expires_in', 'scope'}

    def normalize_scopes(self, scopes):
        return ' '.join(scopes)

    def get_token_scope_names(self, token):
        return scope.to_names(token.scope)
