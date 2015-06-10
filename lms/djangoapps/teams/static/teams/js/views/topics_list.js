;(function (define) {
    'use strict';
    define([
        'backbone',
        'underscore',
        'common/js/components/views/paging',
        'common/js/components/views/paging_header',
        'common/js/components/views/paging_footer',
        'teams/js/views/topic_card'
    ], function (Backbone, _, PagingView, PagingHeaderView, PagingFooterView, TopicCardView) {
        var TopicsListView = Backbone.View.extend({
            initialize: function() {
                this.paging_topic_view = new this.PagingTopicView({
                    collection: this.collection
                });
            },

            render: function() {
                this.$el.html(this.paging_topic_view.renderPageItems().$el);
            },

            PagingTopicView: PagingView.extend({
                initialize: function() {
                    PagingView.prototype.initialize.call(this);
                    this.registerSortableColumn('name', gettext('Name'), 'name', 'asc');
                    this.registerSortableColumn('team_count', gettext('Team Count'), 'team_count', 'desc');
                    this.setInitialSortColumn('name');
                    // Keep track of child views to prevent memory leaks.
                    this.childViews = [];
                    this.headerView = new PagingHeaderView({view: this, collection: this.collection});
                    this.footerView = new PagingFooterView({view: this, collection: this.collection});
                    this.$el.append(this.headerView.render().el);
                    this.$el.append(this.footerView.render().el);
                },
                renderPageItems: function () {
                    var pagingView = this;
                    _.each(pagingView.childViews, function(view) { view.remove(); });
                    pagingView.childViews = [];
                    this.collection.each(function(topic) {
                        var topic_card_view = new TopicCardView({model: topic});
                        pagingView.childViews.push(topic_card_view);
                        topic_card_view.render();
                        pagingView.$el.append(topic_card_view.el);
                    });
                    return this;
                }
            })
        });
        return TopicsListView;
    });
}).call(this, define || RequireJS.define);
