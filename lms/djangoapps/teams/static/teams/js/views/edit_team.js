;(function (define) {
'use strict';

define(['backbone',
        'underscore',
        'gettext',
        'js/views/fields',
        'text!teams/templates/edit-team.underscore'],
       function (Backbone, _, gettext, FieldViews, edit_team_template) {
           return Backbone.View.extend({
               fieldsModel: Backbone.Model.extend({
                    defaults: {
                        name: '',
                        description: '',
                        id: ''
                    },

                    modelValue: function () {
                        return '';
                    }
               }),

               initialize: function(options) {
                   this.teamNameField = new FieldViews.TextFieldView({
                       model: new this.fieldsModel(),
                       title: gettext('Name'),
                       bindEvents: false,
                       helpMessage: gettext("The primary identifier for your teams, limited to 100 characters.")
                   });

                   this.teamDescriptionField = new FieldViews.TextareaFieldView({
                       model: new this.fieldsModel(),
                       title: gettext('Description'),
                       editable: 'always',
                       showMessages: false,
                       bindEvents: false,
                       descriptionMessage: gettext("This describes your team's community goal or directive, encouraging students to be informed before they join.")
                   });

                   this.optionalDescriptionField = new FieldViews.ReadonlyFieldView({
                       model: new this.fieldsModel(),
                       title: gettext('Optional Characteristics'),
                       helpMessage: gettext("You can help students find your tem by specifying your team's characteristics. The more limitations you add, the fewer students may be interested in joining your group, so choose carefully!")
                   });

                   this.teamLanguageField = new FieldViews.DropdownFieldView({
                       model: new this.fieldsModel(),
                       title: gettext('Language Preference'),
                       required: false,
                       showMessages: false,
                       bindEvents: false,
                       titleIconName: 'fa-comment-o',
                       options: [['a', 'A'], ['b', 'B'], ['c', 'C']]
                   });

                   this.teamCountryField = new FieldViews.DropdownFieldView({
                       model: new this.fieldsModel(),
                       title: gettext('Country'),
                       required: false,
                       showMessages: false,
                       bindEvents: false,
                       titleIconName: 'fa-globe',
                       options: [['a', 'A'], ['b', 'B'], ['c', 'C']]
                   });
               },

               render: function() {
                   this.$el.html(_.template(edit_team_template)({topicTitle: gettext("ABC")}));
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
