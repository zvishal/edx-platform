"""
Mixins to facilitate testing OAuth connections to Django-OAuth-Toolkit
"""

# pylint: disable=protected-access

from unittest import skip

from lms.djangoapps.oauth_dispatch import adapters


class DOTAdapterMixin(object):
    """
    Mixin to rewire existing tests to use django-oauth-toolkit (DOT) backend

    Overwrites self.client_id, self.access_token, self.oauth2_adapter
    """

    client_id = 'dot_test_client_id'
    access_token = 'dot_test_access_token'
    oauth2_adapter = adapters.DOTAdapter()

    @skip("Not supported yet")
    def test_single_access_token(self):
        pass

    @skip("Not supported yet")
    def test_scopes(self):
        pass


class DOPAdapterMixin(object):
    """
    Mixin to rewire existing tests to use django-oauth2-provider (DOP) backend

    Overwrites self.client_id, self.access_token, self.oauth2_adapter
    """
    client_id = 'dop_test_client_id'
    access_token = 'dop_test_access_token'
    oauth2_adapter = adapters.DOPAdapter()
