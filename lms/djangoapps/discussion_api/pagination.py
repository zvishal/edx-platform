"""
Discussion API pagination support
"""


def get_paginated_data(request, results, page_num, per_page):
    """
    Return a dict with the following values:

    next: The URL for the next page
    previous: The URL for the previous page
    results: The results on this page
    """
    # TODO
    return {
        "next": "http://www.example.com",
        "previous": "http://www.example.com",
        "results": results
    }
