from django.conf import settings
from django.core.urlresolvers import clear_url_caches, resolve

from django.test import TestCase
from django.test.utils import override_settings

from path import Path

from nose.plugins.attrib import attr

import sys

RED_THEME_DIR = Path("/edx/app/edxapp/edx-platform/themes/red-theme")


@attr('shard_1')
class FaviconTestCase(TestCase):

    def setUp(self):
        super(FaviconTestCase, self).setUp()

    def test_favicon_redirect(self):
        resp = self.client.get("/favicon.ico")
        self.assertEqual(resp.status_code, 301)
        self.assertRedirects(
            resp,
            "/static/images/favicon.ico",
            status_code=301, target_status_code=404  # @@@ how to avoid 404?
        )

    @override_settings(FAVICON_PATH="images/foo.ico")
    def test_favicon_redirect_with_favicon_path_setting(self):

        # for some reason I had to put this inline rather than just using
        # the UrlResetMixin

        urlconf = settings.ROOT_URLCONF
        if urlconf in sys.modules:
            reload(sys.modules[urlconf])
        clear_url_caches()
        resolve("/")

        resp = self.client.get("/favicon.ico")
        self.assertEqual(resp.status_code, 301)
        self.assertRedirects(
            resp,
            "/static/images/foo.ico",
            status_code=301, target_status_code=404  # @@@ how to avoid 404?
        )

    @override_settings(COMPREHENSIVE_THEME_DIR=RED_THEME_DIR)
    def test_favicon_redirect_with_theme(self):
        self.assertEqual(settings.COMPREHENSIVE_THEME_DIR, RED_THEME_DIR)

        resp = self.client.get("/favicon.ico")
        self.assertEqual(resp.status_code, 301)
        self.assertRedirects(
            resp,
            "/static/images/foo.ico",
            status_code=301, target_status_code=404  # @@@ how to avoid 404?
        )
