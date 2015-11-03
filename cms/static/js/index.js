define(["domReady", "jquery", "underscore", "js/utils/cancel_on_escape", "js/views/utils/create_course_utils",
    "js/views/utils/create_library_utils", "common/js/components/utils/view_utils"],
    function (domReady, $, _, CancelOnEscape, CreateCourseUtilsFactory, CreateLibraryUtilsFactory, ViewUtils) {
        "use strict";
        var CreateCourseUtils = new CreateCourseUtilsFactory({
            name: '.new-course-name',
            org: '.new-course-org',
            number: '.new-course-number',
            run: '.new-course-run',
            save: '.new-course-save',
            errorWrapper: '.create-course .wrap-error',
            errorMessage: '#course_creation_error',
            tipError: '.create-course span.tip-error',
            error: '.create-course .error',
            allowUnicode: '.allow-unicode-course-id'
        }, {
            shown: 'is-shown',
            showing: 'is-showing',
            hiding: 'is-hiding',
            disabled: 'is-disabled',
            error: 'error'
        });

        var CreateLibraryUtils = new CreateLibraryUtilsFactory({
            name: '.new-library-name',
            org: '.new-library-org',
            number: '.new-library-number',
            save: '.new-library-save',
            errorWrapper: '.create-library .wrap-error',
            errorMessage: '#library_creation_error',
            tipError: '.create-library  span.tip-error',
            error: '.create-library .error',
            allowUnicode: '.allow-unicode-library-id'
        }, {
            shown: 'is-shown',
            showing: 'is-showing',
            hiding: 'is-hiding',
            disabled: 'is-disabled',
            error: 'error'
        });

        var saveNewCourse = function (e) {
            e.preventDefault();

            if (CreateCourseUtils.hasInvalidRequiredFields()) {
                return;
            }

            var $newCourseForm = $(this).closest('#create-course-form');
            var display_name = $newCourseForm.find('.new-course-name').val();
            var org = $newCourseForm.find('.new-course-org').val();
            var number = $newCourseForm.find('.new-course-number').val();
            var run = $newCourseForm.find('.new-course-run').val();

            var course_info = {
                org: org,
                number: number,
                display_name: display_name,
                run: run
            };

            analytics.track('Created a Course', course_info);
            CreateCourseUtils.create(course_info, function (errorMessage) {
                $('.create-course .wrap-error').addClass('is-shown');
                $('#course_creation_error').html('<p>' + errorMessage + '</p>');
                $('.new-course-save').addClass('is-disabled').attr('aria-disabled', true);
            });
        };

        var makeCancelHandler = function (addType) {
            return function(e) {
                e.preventDefault();
                $('.new-'+addType+'-button').removeClass('is-disabled').attr('aria-disabled', false);
                $('.wrapper-create-'+addType).removeClass('is-shown');
                // Clear out existing fields and errors
                $('#create-'+addType+'-form input[type=text]').val('');
                $('#'+addType+'_creation_error').html('');
                $('.create-'+addType+' .wrap-error').removeClass('is-shown');
                $('.new-'+addType+'-save').off('click');
            };
        };

        var addNewCourse = function (e) {
            e.preventDefault();
            $('.new-course-button').addClass('is-disabled').attr('aria-disabled', true);
            $('.new-course-save').addClass('is-disabled').attr('aria-disabled', true);
            var $newCourse = $('.wrapper-create-course').addClass('is-shown');
            var $cancelButton = $newCourse.find('.new-course-cancel');
            var $courseName = $('.new-course-name');
            $courseName.focus().select();
            $('.new-course-save').on('click', saveNewCourse);
            $cancelButton.bind('click', makeCancelHandler('course'));
            CancelOnEscape($cancelButton);

            CreateCourseUtils.configureHandlers();
        };

        var saveNewLibrary = function (e) {
            e.preventDefault();

            if (CreateLibraryUtils.hasInvalidRequiredFields()) {
                return;
            }

            var $newLibraryForm = $(this).closest('#create-library-form');
            var display_name = $newLibraryForm.find('.new-library-name').val();
            var org = $newLibraryForm.find('.new-library-org').val();
            var number = $newLibraryForm.find('.new-library-number').val();

            var lib_info = {
                org: org,
                number: number,
                display_name: display_name,
            };

            analytics.track('Created a Library', lib_info);
            CreateLibraryUtils.create(lib_info, function (errorMessage) {
                $('.create-library .wrap-error').addClass('is-shown');
                $('#library_creation_error').html('<p>' + errorMessage + '</p>');
                $('.new-library-save').addClass('is-disabled').attr('aria-disabled', true);
            });
        };

        var addNewLibrary = function (e) {
            e.preventDefault();
            $('.new-library-button').addClass('is-disabled').attr('aria-disabled', true);
            $('.new-library-save').addClass('is-disabled').attr('aria-disabled', true);
            var $newLibrary = $('.wrapper-create-library').addClass('is-shown');
            var $cancelButton = $newLibrary.find('.new-library-cancel');
            var $libraryName = $('.new-library-name');
            $libraryName.focus().select();
            $('.new-library-save').on('click', saveNewLibrary);
            $cancelButton.bind('click', makeCancelHandler('library'));
            CancelOnEscape($cancelButton);

            CreateLibraryUtils.configureHandlers();
        };

        var showTab = function(tab) {
          return function(e) {
            e.preventDefault();
            $('.courses-tab').toggleClass('active', tab === 'courses');
            $('.libraries-tab').toggleClass('active', tab === 'libraries');
            $('.xblocks-tab').toggleClass('active', tab === 'xblocks');
            // Also toggle this course-related notice shown below the course tab, if it is present:
            $('.wrapper-creationrights').toggleClass('is-hidden', tab === 'libraries');
          };
        };

        var toggleXBlockDetails = function(e) {
            e.preventDefault();
            $(this).siblings('.details-block').toggle(500);
            $(this).toggleClass('fa-chevron-down').toggleClass('fa-chevron-up');
        };

        var ratingsToStars = function() {
            var $ratingElem = $(this);
            var rating = $ratingElem.text() / 2.00;
            $ratingElem.html('');
            for (var i = 0; i < Math.floor(rating); i++) {
                $ratingElem.append('<span class="icon fa fa-star"></span>');
            }
            if ((rating%1) > 0) {
               $ratingElem.append('<span class="icon fa fa-star-half"></span>'); 
            }
            $ratingElem.show();
        };

        var installXblock = function(e) {
            e.preventDefault();
            var $self = $(this);
            var $buttons = $('.xblocks-tab .install-button');
            var githublink = $self.data('githublink');
            var name = $self.data('xblockname');
            var action = $self.data('xaction');
            if(!$self.hasClass('disabled')) {
                $buttons.addClass('disabled');
                $.ajax({
                    url: window.location.href, 
                    type: 'POST', 
                    cache: false, 
                    data: {
                        xblockname: name,
                        githublink: githublink, 
                        xaction: action
                    },
                    success: function(data) {
                        var installedIcon = $self.parents('.course-item').find('.installed-icon');
                        installedIcon.toggleClass('fa-square-o').toggleClass('fa-square');
                        if(action === 'install') {
                            $self.text('Remove');
                            $self.data('xaction', 'remove');
                        }
                        else {
                            $self.text('Install');
                            $self.data('xaction', 'install');                        
                        }
                    }, 
                    complete: function() {
                        $buttons.removeClass('disabled');
                    }
                });
            }
        };

        var filterXblocksList = function () {
            var searchTerm = $(this).val().toLowerCase();
            $('.xblocks-tab .xblock-title').each(function () {
                var xblockName = $(this).text().toLowerCase();
                if (xblockName.indexOf(searchTerm) >= 0) {
                    $(this).parents('.course-item').show();
                }
                else {
                    $(this).parents('.course-item').hide();
                }
            });
        };

        var onReady = function () {
            $('.new-course-button').bind('click', addNewCourse);
            $('.new-library-button').bind('click', addNewLibrary);
            $('.dismiss-button').bind('click', ViewUtils.deleteNotificationHandler(function () {
                ViewUtils.reload();
            }));
            $('.action-reload').bind('click', ViewUtils.reload);
            $('#course-index-tabs .courses-tab').bind('click', showTab('courses'));
            $('#course-index-tabs .libraries-tab').bind('click', showTab('libraries'));
            $('#course-index-tabs .xblocks-tab').bind('click', showTab('xblocks'));
            $('.xblocks-tab .details-icon').bind('click', toggleXBlockDetails);
            $('.xblocks-tab .rating-icon').each(ratingsToStars);
            $('.xblocks-tab .install-button').bind('click', installXblock);
            $('.xblocks-filter-input').bind('keyup', filterXblocksList);
        };

        domReady(onReady);

        return {
            onReady: onReady
        };
    });
