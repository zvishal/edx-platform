from django.conf.urls import patterns, url
from django.conf import settings

urlpatterns = []

urlpatterns += patterns(
    'student_account.views',
    url(r'^finish_auth$', 'finish_auth', name='finish_auth'),
    url(r'^password$', 'password_change_request_handler', name='password_change_request'),
    url(r'^settings$', 'account_settings', name='account_settings'),
)
