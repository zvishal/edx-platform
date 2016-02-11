"""
    Helpers for accessing comprehensive theming related variables.
"""
from microsite_configuration import microsite
from microsite_configuration import page_title_breadcrumbs
from django.conf import settings


def get_page_title_breadcrumbs(*args):
    """
    This is a proxy function to hide microsite_configuration behind comprehensive theming.
    """
    return page_title_breadcrumbs(*args)


def get_value(val_name, default=None, **kwargs):
    """
    This is a proxy function to hide microsite_configuration behind comprehensive theming.
    """
    return microsite.get_value(val_name, default=default, **kwargs)


def get_template_path(relative_path, **kwargs):
    """
    This is a proxy function to hide microsite_configuration behind comprehensive theming.
    """
    return microsite.get_template_path(relative_path, **kwargs)


def is_request_in_themed_site():
    """
    This is a proxy function to hide microsite_configuration behind comprehensive theming.
    """
    return microsite.is_request_in_microsite()
