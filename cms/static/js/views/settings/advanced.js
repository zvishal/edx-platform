define(["js/views/validation", "jquery", "underscore", "gettext", "codemirror", "js/views/modals/validation_error_modal"],
    function(ValidatingView, $, _, gettext, CodeMirror, ValidationErrorModal) {

var AdvancedView = ValidatingView.extend({
    error_saving : "error_saving",
    successful_changes: "successful_changes",
    render_deprecated: false,

    // Model class is CMS.Models.Settings.Advanced
    events : {
        'focus :input' : "focusInput",
        'blur :input' : "blurInput", 
        'click .add-advanced-module': "addAdvancedModule"
        // TODO enable/disable save based on validation (currently enabled whenever there are changes)
    },
    initialize : function() {
        this.template = _.template($("#advanced_entry-tpl").text());
        this.selectTemplate = _.template($("#advanced_select-tpl").text());
        this.listenTo(this.model, 'invalid', this.handleValidationError);
        this.render();
    },
    render: function() {
        // catch potential outside call before template loaded
        if (!this.template) return this;

        var listEle$ = this.$el.find('.course-advanced-policy-list');
        listEle$.empty();

        // b/c we've deleted all old fields, clear the map and repopulate
        this.fieldToSelectorMap = {};
        this.selectorToField = {};

        // iterate through model and produce key : value editors for each property in model.get
        var self = this;
        _.each(_.sortBy(_.keys(this.model.attributes), function(key) { return self.model.get(key).display_name; }),
            function(key) {
                if (self.render_deprecated || !self.model.get(key).deprecated) {
                    listEle$.append(self.renderTemplate(key, self.model.get(key)));
                    if(key === 'advanced_modules') {
                        var selector = self.selectTemplate({ key: key, 
                            value : advancedModulesList});
                        listEle$.find('li').append(selector);
                    } 
                }
            });

        var policyValues = listEle$.find('.json');
        _.each(policyValues, this.attachJSONEditor, this);
        return this;
    },
    attachJSONEditor : function (textarea, flag) {
        // Since we are allowing duplicate keys at the moment, it is possible that we will try to attach
        // JSON Editor to a value that already has one. Therefore only attach if no CodeMirror peer exists.
        if ( $(textarea).siblings().hasClass('CodeMirror')) {
            return;
        }

        var self = this;
        var oldValue = $(textarea).val();

        var cm = CodeMirror.fromTextArea(textarea, {
            mode: "application/json",
            lineNumbers: false,
            lineWrapping: false});
        cm.on('change', function(instance, changeobj) {
                instance.save();
                // this event's being called even when there's no change :-(
                if (instance.getValue() !== oldValue) {
                    self.showSaveNotification();
                }
            });
        cm.on('focus', function(mirror) {
              $(textarea).parent().children('label').addClass("is-focused");
            });
        cm.on('blur', function (mirror) {
                $(textarea).parent().children('label').removeClass("is-focused");
                var key = $(mirror.getWrapperElement()).closest('.field-group').children('.key').attr('id');
                var stringValue = $.trim(mirror.getValue());
                // update CodeMirror to show the trimmed value.
                mirror.setValue(stringValue);
                var JSONValue = undefined;
                try {
                    JSONValue = JSON.parse(stringValue);
                } catch (e) {
                    // If it didn't parse, try converting non-arrays/non-objects to a String.
                    // But don't convert single-quote strings, which are most likely errors.
                    var firstNonWhite = stringValue.substring(0, 1);
                    if (firstNonWhite !== "{" && firstNonWhite !== "[" && firstNonWhite !== "'") {
                        try {
                            stringValue = '"'+stringValue +'"';
                            JSONValue = JSON.parse(stringValue);
                            mirror.setValue(stringValue);
                        } catch(quotedE) {
                            // TODO: validation error
                            // console.log("Error with JSON, even after converting to String.");
                            // console.log(quotedE);
                            JSONValue = undefined;
                        }
                    }
                }
                if (JSONValue !== undefined) {
                    var modelVal = self.model.get(key);
                    modelVal.value = JSONValue;
                    self.model.set(key, modelVal);
                }
            });
    },
    saveView : function() {
        // TODO one last verification scan:
        //    call validateKey on each to ensure proper format
        //    check for dupes
        var self = this;
        this.model.save({}, {
            success : function() {
                self.render();
                var title = gettext("Your policy changes have been saved.");
                var message = gettext("Please note that validation of your policy key and value pairs is not currently in place yet. If you are having difficulties, please review your policy pairs.");
                self.showSavedBar(title, message);
                analytics.track('Saved Advanced Settings', {
                    'course': course_location_analytics
                });
            },
            silent: true,
            error: function(model, response, options) {
                var json_response, reset_callback, err_modal;

                /* Check that the server came back with a bad request error*/
                if (response.status === 400) {
                    json_response = $.parseJSON(response.responseText);
                    reset_callback = function() {
                        self.revertView();
                    };

                    /* initialize and show validation error modal */
                    err_modal = new ValidationErrorModal();
                    err_modal.setContent(json_response);
                    err_modal.setResetCallback(reset_callback);
                    err_modal.show();
                }
            }
        });
    },
    revertView: function() {
        var self = this;
        this.model.fetch({
            success: function() { self.render(); },
            reset: true
        });
    },
    renderTemplate: function (key, model) {
        var newKeyId = _.uniqueId('policy_key_'),
        newEle = this.template({ key: key, display_name : model.display_name, help: model.help,
            value : JSON.stringify(model.value, null, 4), deprecated: model.deprecated,
            keyUniqueId: newKeyId, valueUniqueId: _.uniqueId('policy_value_')});
        this.fieldToSelectorMap[key] = newKeyId;
        this.selectorToField[newKeyId] = key;
        return newEle;
    },
    addAdvancedModule: function(event) {
        event.preventDefault();
        var $elem = $(event.target);
        var $parent = $elem.parents('li');
        var $textarea = $parent.find('textarea.json');
        var module = $parent.find('select').find(":selected").text();
        var advancedTextBox = $textarea.val();
        var list = $.parseJSON(advancedTextBox);
        list.push(module);
        $textarea.html(JSON.stringify(list, null, 4)).show();
        $parent.find('.CodeMirror.cm-s-default').off().remove();
        this.attachJSONEditor($textarea[0], true);
        this.showSaveNotification();
    },
    focusInput : function(event) {
        $(event.target).prev().addClass("is-focused");
    },
    blurInput : function(event) {
        $(event.target).prev().removeClass("is-focused");
    }, 
    showSaveNotification: function() {
        var message = gettext("Your changes will not take effect until you save your progress. Take care with key and value formatting, as validation is not implemented.");
        this.showNotificationBar(message,
                                 _.bind(this.saveView, this),
                                 _.bind(this.revertView, this));
    }
});

return AdvancedView;
});
