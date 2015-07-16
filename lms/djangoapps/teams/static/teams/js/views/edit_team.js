;(function (define) {
'use strict';

define(['backbone',
        'underscore',
        'gettext',
        'js/views/fields',
        'teams/js/models/team',
        'text!teams/templates/edit-team.underscore'],
       function (Backbone, _, gettext, FieldViews, TeamModel, edit_team_template) {
           return Backbone.View.extend({

               initialize: function(options) {
                   this.topicName = options.topicName;
                   this.languages = options.languages;
                   this.countries = options.countries;

                   this.teamNameField = new FieldViews.TextFieldView({
                       model: new TeamModel(),
                       title: gettext('Name'),
                       valueAttribute: 'name',
                       bindEvents: false,
                       helpMessage: gettext("The primary identifier for your teams, limited to 100 characters.")
                   });

                   this.teamDescriptionField = new FieldViews.TextareaFieldView({
                       model: new TeamModel(),
                       title: gettext('Description'),
                       valueAttribute: 'description',
                       editable: 'always',
                       showMessages: false,
                       bindEvents: false,
                       descriptionMessage: gettext("This describes your team's community goal or directive, encouraging students to be informed before they join.")
                   });

                   this.optionalDescriptionField = new FieldViews.ReadonlyFieldView({
                       model: new TeamModel(),
                       title: gettext('Optional Characteristics'),
                       helpMessage: gettext("You can help students find your tem by specifying your team's characteristics. The more limitations you add, the fewer students may be interested in joining your group, so choose carefully!")
                   });

                   this.teamLanguageField = new FieldViews.DropdownFieldView({
                       model: new TeamModel(),
                       title: gettext('Language Preference'),
                       valueAttribute: 'language',
                       required: false,
                       showMessages: false,
                       bindEvents: false,
                       titleIconName: 'fa-comment-o',
                       options: this.languages
                   });

                   this.teamCountryField = new FieldViews.DropdownFieldView({
                       model: new TeamModel(),
                       title: gettext('Country'),
                       valueAttribute: 'country',
                       required: false,
                       showMessages: false,
                       bindEvents: false,
                       titleIconName: 'fa-globe',
                       options: this.countries
                   });
               },

               render: function() {
                   this.$el.html(_.template(edit_team_template)({topicName: gettext(this.topicName)}));
                   this.assign(this.teamNameField, '.team-name');
                   this.assign(this.teamDescriptionField, '.team-description');
                   this.assign(this.optionalDescriptionField, '.team-optional-fields-descriptions');
                   this.assign(this.teamLanguageField, '.team-language');
                   this.assign(this.teamCountryField, '.team-country');
                   return this;
               },

               assign: function(view, selector) {
                   view.setElement(this.$(selector)).render();
               }
           });
       });
}).call(this, define || RequireJS.define);
