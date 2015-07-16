;(function (define) {
    'use strict';
    define([
        'backbone',
        'teams/js/views/team_card',
        'common/js/components/views/paginated_view',
        'teams/js/views/create_team'
    ], function (Backbone, TeamCardView, PaginatedView, CreateTeamView) {
        var TeamsView = PaginatedView.extend({
            type: 'teams',
            cardView: TeamCardView,

            events: {
                'click button.action': 'showCreateTeamForm' // entry point for team creation
            },

            initialize: function (options) {
                PaginatedView.prototype.initialize.call(this, options);
                this.topicName = options.topicName;
                this.languages = options.languages;
                this.countries = options.countries;
            },

            render: function () {
                PaginatedView.prototype.render.call(this);

                this.$el.append(
                    $('<button class="action action-primary">' + gettext('Create new team') + '</button>')
                );
                return this;
            },

            showCreateTeamForm: function () {
                var view = new CreateTeamView({
                    el: $('.teams-content'),
                    topicName: this.topicName,
                    languages: this.languages,
                    countries: this.countries,
                    fragment: Backbone.history.fragment,
                    href: Backbone.history.location.href
                });
                view.render();
            }
        });
        return TeamsView;
    });
}).call(this, define || RequireJS.define);
