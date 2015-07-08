;(function (define) {
    'use strict';

    define(['jquery', 'teams/js/views/teams_tab'],
        function ($, TeamsTabView) {
            return function (topics, topics_url, teams_url, course_id) {
                (new TeamsTabView({
                    el: $('.teams-content'),
                    topics: topics,
                    topics_url: topics_url,
                    teams_url: teams_url,
                    course_id: course_id
                })).render();
                Backbone.history.start();
            };
        });
}).call(this, define || RequireJS.define);
