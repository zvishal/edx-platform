;(function (define) {
    'use strict';
    define([
        'teams/js/views/topic_card',
        'common/js/components/views/paginated_view'
    ], function (TopicCardView, PaginatedView) {
        var TopicsView = PaginatedView.extend({
            type: 'topics',
            cardView: TopicCardView
        });
        return TopicsView;
    });
}).call(this, define || RequireJS.define);
