;(function (define) {
'use strict';

define(['backbone',
        'underscore',
        'gettext',
        'js/components/header/models/header',
        'js/components/header/views/header',
        'teams/js/views/edit_team'],
       function (Backbone, _, gettext, HeaderModel, HeaderView, TeamEditView) {
           return Backbone.View.extend({
               initialize: function(options) {
                   this.headerModel = new HeaderModel({
                       description: gettext("Create a new team when you can't find existing teams to join, or if you would like to learn with friends you know."),
                       title: gettext("New Team"),
                       breadcrumbs: this.constructBreadcurmbs(options.fragment, options.href)
                   });

                   this.headerView = new HeaderView({
                       model: this.headerModel,
                       events: {
                           'click nav.breadcrumbs a.nav-item': function (event) {
                               //event.preventDefault();
                               console.log(Backbone.history);
                               Backbone.history.navigate('topics/algorithms', {trigger: true});
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
               },

               constructBreadcurmbs: function (fragment, href) {
                   return [
                       {
                           title: fragment.split('/').pop(),
                           url: href
                       }
                   ];
               }
           });
       });
}).call(this, define || RequireJS.define);
