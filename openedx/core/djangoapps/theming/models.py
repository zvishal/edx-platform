"""
Comprehensive Theme related models.
"""
from django.db import models
from django.contrib.sites.models import Site


class SiteTheme(models.Model):
    """
    This is where the information about the site's theme gets stored to the db.
    """
    site = models.ForeignKey(Site, related_name='themes')
    theme_dir_name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.theme_dir_name
