;(function (define) {
    'use strict';
    define([
        'backbone',
        'underscore',
        'teams/js/views/team_card',
        'common/js/components/views/list',
        'common/js/components/views/paging_header',
        'common/js/components/views/paging_footer',
        'text!teams/templates/teams.underscore'
    ], function (Backbone, _, TeamCardView, ListView, PagingHeader, PagingFooter, teamsTemplate) {
        var TeamsListView = ListView.extend({
            tagName: 'div',
            className: 'teams-container',
            itemViewClass: TeamCardView
        });

        var TeamsView = Backbone.View.extend({
            initialize: function () {
                this.listView  = new TeamsListView({collection: this.collection});
                this.headerView = new PagingHeader({collection: this.collection});
                this.footerView = new PagingFooter({
                    collection: this.collection,
                    hideWhenOnePage: true
                });
                this.collection.on('page_changed', function () {
                    this.$('.sr-is-focusable.sr-teams-view').focus()
                }, this);
            },

            render: function () {
                this.$el.html(_.template(teamsTemplate));
                this.assign(this.listView, '.teams-list');
                this.assign(this.headerView, '.teams-paging-header');
                this.assign(this.footerView, '.teams-paging-footer');
                return this;
            },

            assign: function (view, selector) {
                view.setElement(this.$(selector)).render();
            }
        });

        return TeamsView;
    });
}).call(this, define || RequireJS.define);
