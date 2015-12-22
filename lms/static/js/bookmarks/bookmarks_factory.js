;(function (define) {
    'use strict';
    define([
            'js/bookmarks/views/bookmarks_list_button',
            'js/bookmarks/views/bookmark_button' // Needed by vertical module
        ],
        function(BookmarksListButton) {
            return function() {
                return new BookmarksListButton();
            };
        }
    );
}).call(this, define || RequireJS.define);
