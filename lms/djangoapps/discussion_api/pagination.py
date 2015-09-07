"""
Discussion API pagination support
"""
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import pagination


class DiscussionPagination(pagination.PageNumberPagination):
    """TODO """
    page_size = 10
    page_size_query_param = "page_size"

    def get_paginated_response(self, data):
        return Response({
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })


def get_paginated_data(request, results, page_num, per_page):
    """
    Return a dict with the following values:

    next: The URL for the next page
    previous: The URL for the previous page
    results: The results on this page
    """
    paginator = DiscussionPagination()
    paginator.paginate_queryset(results, Request(request))
    return paginator.get_paginated_response(results).data
