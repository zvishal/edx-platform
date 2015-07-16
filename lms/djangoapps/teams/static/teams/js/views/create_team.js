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
                       title: gettext("New Team")
                   });

                   this.headerView = new HeaderView({
                       model: this.headerModel
                   });

                   this.editView = new TeamEditView({
                       className: 'create-new-team'
                   });
               },

               render: function() {
                   this.$el.append(this.headerView.$el);
                   this.headerView.render();
                   this.$el.append(this.editView.$el);
                   this.editView.render();
               }
           });
       });
}).call(this, define || RequireJS.define);
