;(function (define) {
'use strict';

define(['backbone',
        'underscore',
        'gettext',
        'js/components/header/models/header',
        'js/components/header/views/header',
        'teams/js/views/edit_team',
        'teams/js/views/create_team_actions'],
       function (Backbone, _, gettext, HeaderModel, HeaderView, TeamEditView, CreateTeamActionsView) {
           return Backbone.View.extend({
               initialize: function(options) {
                   this.headerModel = new HeaderModel({
                       description: gettext("Create a new team when you can't find existing teams to join, or if you would like to learn with friends you know."),
                       title: gettext("New Team"),
                       breadcrumbs: [{title: options.topicName, url: options.href}]
                   });

                   this.headerView = new HeaderView({
                       model: this.headerModel,
                       actionsView: new CreateTeamActionsView({}),

                       // As per my understanding we don't need this(`events`) but for
                       // whatever reason click on breadcrumb link is not working without this
                       events: {
                           'click nav.breadcrumbs a.nav-item': function () {
                               Backbone.history.navigate('', {trigger: true});
                           }
                       }
                   });

                   this.editView = new TeamEditView({
                       className: 'create-new-team',
                       topicName: options.topicName,
                       languages: options.languages,
                       countries: options.countries
                   });
               },

               render: function() {
                   this.$el.html('');
                   this.$el.append(this.headerView.$el);
                   this.headerView.render();
                   this.$el.append(this.editView.$el);
                   this.editView.render();
               }
           });
       });
}).call(this, define || RequireJS.define);
