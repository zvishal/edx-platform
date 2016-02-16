(function() {
    'use strict';

    this.AjaxPrefix = {
        addAjaxPrefix: function(jQuery, prefix) {
            jQuery.postWithPrefix = function(url, data, callback, type) {
                return $.post('' + (prefix()) + url, data, callback, type);
            };

            jQuery.getWithPrefix = function(url, data, callback, type) {
                return $.get('' + (prefix()) + url, data, callback, type);
            };

            jQuery.ajaxWithPrefix = function(url, settings) {
                if (settings !== null) {
                    return $.ajax('' + (prefix()) + url, settings);
                } else {
                    settings = url;
                    settings.url = '' + (prefix()) + settings.url;
                    return $.ajax(settings);
                }
            };

            return jQuery.ajaxWithPrefix;
        }
    };

}).call(this);
