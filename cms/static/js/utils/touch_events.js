(function() {
    'use strict';

    define([
        'domReady',
        'jquery'
    ],
    function(domReady, $) {
        var touchEvents = function() {

            var onTouchBasedDevice = function() {
                return navigator.userAgent.match(/iPhone|iPod|iPad|Android/i);
            };

            window.onTouchBasedDevice = onTouchBasedDevice;

            return domReady(function() {
                if (onTouchBasedDevice()) {
                    return $('body').addClass('touch-based-device');
                }
            });
        }();

        return touchEvents;
    });

}).call(this);
