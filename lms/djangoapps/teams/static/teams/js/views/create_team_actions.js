;(function (define) {
'use strict';

define(['backbone',
        'underscore',
        'gettext',
        'text!teams/templates/create-team-actions.underscore'],
       function (Backbone, _, gettext, create_team_actions_template) {
           return Backbone.View.extend({

               initialize: function(options) {
               },

               render: function() {
                   this.$el.html(_.template(create_team_actions_template));
                   return this;
               }
           });
       });
}).call(this, define || RequireJS.define);
