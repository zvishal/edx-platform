;(function (define) {
    'use strict';

    define(['backbone',
            'underscore',
            'gettext',
            'js/components/header/views/header',
            'js/components/header/models/header',
            'js/components/tabbed/views/tabbed_view',
            'teams/js/views/topics',
            'teams/js/collections/topic'],
           function (Backbone, _, gettext, HeaderView, HeaderModel, TabbedView, TopicsView, TopicCollection) {
               var TeamTabView = Backbone.View.extend({
                   initialize: function(options) {
                       this.headerModel = new HeaderModel({
                           description: gettext("Course teams are organized into topics created by course instructors. Try to join others in an existing team before you decide to create a new team!"),
                           title: gettext("Teams")
                       });
                       this.headerView = new HeaderView({
                           model: this.headerModel
                       });
                       // TODO replace this with actual views!
                       var TempTabView = Backbone.View.extend({
                           initialize: function (options) {
                               this.text = options.text;
                           },

                           render: function () {
                               this.$el.text(this.text);
                           }
                       });
                       this.tabbedView = new TabbedView({
                           tabs: [{
                               title: gettext('My Teams'),
                               url: 'teams',
                               view: new TempTabView({text: 'This is the new Teams tab.'})
                           }, {
                               title: gettext('Browse'),
                               url: 'browse',
                               view: new TopicsView({
                                   collection: new TopicCollection(
                                       options.topics,
                                       {url: options.topics_url, course_id: options.course_id, parse: true}
                                   ).bootstrap()
                               })
                           }]
                       });
                       Backbone.history.start();
                   },

                   render: function() {
                       this.$el.append(this.headerView.$el);
                       this.headerView.render();
                       this.$el.append(this.tabbedView.$el);
                       this.tabbedView.render();
                   }
               });

               return TeamTabView;
           });
}).call(this, define || RequireJS.define);
