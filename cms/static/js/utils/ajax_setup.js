(function() {
    'use strict';

    define([
        'domReady',
        'jquery',
        'underscore.string',
        'backbone',
        'gettext',
        'common/js/components/views/feedback_notification',
        'common/static/common/js/utils/ajax_prefix',
        'jquery.cookie'
    ],
    function(domReady, $, str, Backbone, gettext, NotificationView) {
        var ajaxSetup = function() {
            AjaxPrefix.addAjaxPrefix(jQuery, function() {
                return $('meta[name="path_prefix"]').attr('content');
            });

            window.CMS = window.CMS || {};
            CMS.URL = CMS.URL || {};

            _.extend(CMS, Backbone.Events);
            Backbone.emulateHTTP = true;

            $.ajaxSetup({
                headers: {
                    'X-CSRFToken': $.cookie('csrftoken')
                },
                dataType: 'json'
            });

            $(document).ajaxError(function(event, jqXHR, ajaxSettings) {
                var message, 
                    msg;

                if (ajaxSettings.notifyOnError === false) {
                    return;
                }

                if (jqXHR.responseText) {
                    try {
                        message = JSON.parse(jqXHR.responseText).error;
                    } catch (error) {
                        message = str.truncate(jqXHR.responseText, 300);
                    }
                } else {
                    message = gettext('This may be happening because of an error with our server or your internet connection. Try refreshing the page or making sure you are online.');
                }

                msg = new NotificationView.Error({
                    'title': gettext('Studio\'s having trouble saving your work'),
                        'message': message
                });

                return msg.show();
            });

            $.postJSON = function(url, data, callback) {
                if ($.isFunction(data)) {
                    callback = data;
                    data = undefined;
                }

                return $.ajax({
                    url: url,
                    type: 'POST',
                    contentType: 'application/json; charset=utf-8',
                    dataType: 'json',
                    data: JSON.stringify(data),
                    success: callback
                });
            };
        }();

        return ajaxSetup;
    });

}).call(this);
