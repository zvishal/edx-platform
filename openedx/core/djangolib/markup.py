"""
Utilities for use in Mako markup.
"""

import markupsafe


# So that we can use escape() imported from here.
escape = markupsafe.escape  # pylint: disable=invalid-name


def HTML(html):                                 # pylint: disable=invalid-name
    """
    Mark a string as already HTML, so that it won't be escaped before output.

    Use this function when formatting HTML into other strings.  It must be
    used in conjunction with ``escape()``, and both ``HTML()`` and ``escape()``
    must be closed before any calls to ``format()``::

        <%!
        from django.utils.translation import ugettext as _

        from openedx.core.djangolib.markup import escape, HTML
        %>
        <%page expression_filter="h"/>
        ${escape(_("Write & send {start}email{end}")).format(
            start=HTML("<a href='mailto:{}'>".format(user.email),
            end=HTML("</a>"),
           )}

    """
    return markupsafe.Markup(html)
