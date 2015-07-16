;(function (define) {
    'use strict';

    define(['backbone',
            'underscore',
            'gettext',
            'js/components/header/views/header',
            'js/components/header/models/header',
            'js/components/tabbed/views/tabbed_view',
            'teams/js/views/topics',
            'teams/js/collections/topic',
            'teams/js/views/teams',
            'teams/js/collections/team',
            'text!teams/templates/teams_tab.underscore'],
           function (Backbone, _, gettext, HeaderView, HeaderModel, TabbedView,
                     TopicsView, TopicCollection, TeamsView, TeamCollection, teamsTemplate) {
               var ViewWithHeader = Backbone.View.extend({
                   initialize: function (options) {
                       this.header = options.header;
                       this.main = options.main;
                   },

                   render: function () {
                       this.$el.html(_.template(teamsTemplate));
                       this.header.setElement(this.$('.teams-header')).render();
                       this.main.setElement(this.$('.teams-main')).render();
                       return this;
                   }
               });

               var TeamTabView = Backbone.View.extend({
                   initialize: function(options) {
                       var TempTabView, router;
                       this.course_id = options.course_id;
                       this.topics = options.topics;
                       this.teams_url = options.teams_url;
                       this.languages = options.languages;
                       this.countries = options.countries;
                       // This slightly tedious approach is necessary
                       // to use regular expressions within Backbone
                       // routes, allowing us to capture which tab
                       // name is being routed to
                       router = this.router = new Backbone.Router();
                       _.each([
                           [':default', _.bind(this.routeNotFound, this)],
                           ['topics/:topic_id', _.bind(this.goToTopic, this)],
                           [new RegExp('^(browse)$'), _.bind(this.goToTab, this)],
                           [new RegExp('^(teams)$'), _.bind(this.goToTab, this)]
                       ], function (route) {
                           router.route.apply(router, route);
                       });
                       // TODO replace this with actual views!
                       TempTabView = Backbone.View.extend({
                           initialize: function (options) {
                               this.text = options.text;
                           },

                           render: function () {
                               this.$el.text(this.text);
                           }
                       });
                       this.topicsCollection = new TopicCollection(
                           this.topics,
                           {url: options.topics_url, course_id: this.course_id, parse: true}
                       ).bootstrap();
                       this.mainView = this.tabbedView = new ViewWithHeader({
                           header: new HeaderView({
                               model: new HeaderModel({
                                   description: gettext("Course teams are organized into topics created by course instructors. Try to join others in an existing team before you decide to create a new team!"),
                                   title: gettext("Teams")
                               })
                           }),
                           main: new TabbedView({
                               tabs: [{
                                   title: gettext('My Teams'),
                                   url: 'teams',
                                   view: new TempTabView({text: 'This is the new Teams tab.'})
                               }, {
                                   title: gettext('Browse'),
                                   url: 'browse',
                                   view: new TopicsView({
                                       collection: this.topicsCollection,
                                       router: this.router
                                   })
                               }],
                               router: this.router
                           })
                       });
                   },

                   render: function() {
                       this.mainView.setElement(this.$el).render();
                       return this;
                   },

                   /**
                    * Render the list of teams for the given topic ID.
                    */
                   goToTopic: function (topicID) {
                       // Lazily load the teams-for-topic view in
                       // order to avoid making an extra AJAX call.
                       if (this.teamsView === undefined ||
                           this.teamsView.main.collection.topic_id !== topicID) {
                           var teamCollection = new TeamCollection([], {
                               course_id: this.course_id,
                               url: this.teams_url,
                               topic_id: topicID,
                               per_page: 10
                           }),
                               topic = this.topicsCollection.findWhere({'id': topicID}),
                               self = this,
                               headerView;
                           // The user tried to go to a topic that doesn't exist
                           if (topic === undefined) {
                               this.topicNotFound(topicID);
                               return;
                           }
                           headerView = new HeaderView({
                               model: new HeaderModel({
                                   description: _.escape(topic.get('description')),
                                   title: _.escape(topic.get('name')),
                                   breadcrumbs: [{
                                       title: 'All topics',
                                       url: '#'
                                   }]
                               }),
                               events: {
                                   'click nav.breadcrumbs a.nav-item': function (event) {
                                       event.preventDefault();
                                       self.router.navigate('browse', {trigger: true});
                                   }
                               }
                           });
                           var successCb = function (collection) {
                               self.mainView = self.teamsView = new ViewWithHeader({
                                   header: headerView,
                                   main: new TeamsView({
                                       collection: collection,
                                       topicName: topic.get('name'),
                                       languages: self.languages,
                                       countries: self.countries
                                   })
                               });
                               self.render();
                           };
                           teamCollection.goTo(1, {
                               success: successCb,
                               error: function (collection, response) {
                                   // Topic does not exist
                                   if (response.status === 400) {
                                       self.topicNotFound(topicID);
                                   }
                                   // No teams associated with this topic
                                   else if (response.status === 404) {
                                       collection.totalPages = 0;
                                       successCb(collection);
                                   }
                               }
                           });
                       }
                       else {
                           this.mainView = this.teamsView;
                           this.render();
                       }
                    },

                   /**
                    * Set up the tabbed view and switch tabs.
                    */
                   goToTab: function (tab) {
                       this.mainView = this.tabbedView;
                       // Note that `render` should be called first so
                       // that the tabbed view's element is set
                       // correctly.
                       this.render();
                       this.tabbedView.main.setActiveTab(tab);
                   },

                   // Error handling

                   routeNotFound: function (route) {
                       this.notFoundError(
                           interpolate(
                               gettext('The page %(route)s could not be found.'),
                               {route: route},
                               true
                           )
                       );
                   },

                   topicNotFound: function (topicID) {
                       this.notFoundError(
                           interpolate(
                               gettext('The topic %(topic)s could not be found.'),
                               {topic: topicID},
                               true
                           )
                       );
                   },

                   /**
                    * Called when the user attempts to navigate to a
                    * route that doesn't exist. "Redirects" back to
                    * the main teams tab, and adds an error message.
                    */
                   notFoundError: function (message) {
                       this.router.navigate('teams', {trigger: true});
                       this.$el.prepend($('<p class="error">' + message + '</p>')); // TODO needs styling of error message
                   }
               });

               return TeamTabView;
           });
}).call(this, define || RequireJS.define);
