// Karma configuration
// Generated on Thu Apr 02 2015 20:02:45 GMT-0400 (EDT)

module.exports = function(config) {
  config.set({

    // base path that will be used to resolve all patterns (eg. files, exclude)
    basePath: 'cms/static',


    // frameworks to use
    // available frameworks: https://npmjs.org/browse/keyword/karma-adapter
    frameworks: ['jasmine', 'requirejs'],


    // list of files / patterns to load in the browser
    files: [


          {pattern: 'xmodule_js/common_static/js/vendor/require.js'},
    {pattern: 'xmodule_js/common_static/coffee/src/ajax_prefix.js'},
    {pattern: 'xmodule_js/common_static/js/src/utility.js'},
    {pattern: 'xmodule_js/common_static/js/vendor/jquery.min.js'},
    {pattern: 'xmodule_js/common_static/js/vendor/jquery-ui.min.js'},
    {pattern: 'xmodule_js/common_static/js/vendor/jquery.cookie.js'},
    {pattern: 'xmodule_js/common_static/js/vendor/jquery.simulate.js'},
    {pattern: 'xmodule_js/common_static/js/vendor/underscore-min.js'},
    {pattern: 'xmodule_js/common_static/js/vendor/underscore.string.min.js'},
    {pattern: 'xmodule_js/common_static/js/vendor/backbone-min.js'},
    {pattern: 'xmodule_js/common_static/js/vendor/backbone-associations-min.js'},
    {pattern: 'xmodule_js/common_static/js/vendor/backbone.paginator.min.js'},
    {pattern: 'xmodule_js/common_static/js/vendor/timepicker/jquery.timepicker.js'},
    {pattern: 'xmodule_js/common_static/js/vendor/jquery.leanModal.min.js'},
    {pattern: 'xmodule_js/common_static/js/vendor/jquery.ajaxQueue.js'},
    {pattern: 'xmodule_js/common_static/js/vendor/jquery.form.js'},
    {pattern: 'xmodule_js/common_static/js/vendor/html5-input-polyfills/number-polyfill.js'},
    {pattern: 'xmodule_js/common_static/js/vendor/sinon-1.7.1.js'},
    {pattern: 'xmodule_js/common_static/js/vendor/Squire.js'},
    {pattern: 'xmodule_js/common_static/js/vendor/jasmine-jquery.js'},
    {pattern: 'xmodule_js/common_static/js/vendor/jasmine-stealth.js'},
    {pattern: 'xmodule_js/common_static/js/vendor/jasmine-imagediff.js'},
    {pattern: 'xmodule_js/common_static/js/vendor/jasmine.async.js'},
    {pattern: 'xmodule_js/common_static/js/vendor/CodeMirror/codemirror.js'},
    {pattern: 'xmodule_js/common_static/js/vendor/jQuery-File-Upload/js'},
    {pattern: 'xmodule_js/src/xmodule.js'},
    {pattern: 'xmodule_js/common_static/js/test/i18n.js'},
    {pattern: 'xmodule_js/common_static/js/vendor/draggabilly.pkgd.js'},
    {pattern: 'xmodule_js/common_static/js/vendor/date.js'},
    {pattern: 'xmodule_js/common_static/js/vendor/domReady.js'},
    {pattern: 'xmodule_js/common_static/js/vendor/URI.min.js'},
    {pattern: 'xmodule_js/common_static/js/vendor/jquery.smooth-scroll.min.js'},
    {pattern: 'xmodule_js/common_static/coffee/src/jquery.immediateDescendents.js'},
    {pattern: 'xmodule_js/common_static/js/xblock/**/*.js'},
    // {pattern: 'xmodule_js/common_static/coffee/src/xblock/**/*.coffee'},
    {pattern: 'xmodule_js/common_static/js/vendor/URI.min.js'},
    {pattern: 'xmodule_js/common_static/js/vendor/jQuery-File-Upload/js/jquery.iframe-transport.js'},
    {pattern: 'xmodule_js/common_static/js/vendor/jQuery-File-Upload/js/jquery.fileupload.js'},
    {pattern: 'xmodule_js/common_static/js/vendor/jQuery-File-Upload/js/jquery.fileupload-process.js'},
    {pattern: 'xmodule_js/common_static/js/vendor/jQuery-File-Upload/js/jquery.fileupload-validate.js'},
    {pattern: 'xmodule_js/common_static/js/vendor/mock-ajax.js'},
    // {pattern: 'js/**/*.js'},
    {pattern: 'js/spec/**/*.js'},
    ],


    // list of files to exclude
    exclude: [
    ],


    // preprocess matching files before serving them to the browser
    // available preprocessors: https://npmjs.org/browse/keyword/karma-preprocessor
    preprocessors: {
    },


            plugins:[
            'karma-jasmine',
            'karma-requirejs',
            'karma-firefox-launcher'
//            'karma-phantomjs-launcher',
 //           'karma-coverage',
   //         'karma-sinon'
        ],


    // test results reporter to use
    // possible values: 'dots', 'progress'
    // available reporters: https://npmjs.org/browse/keyword/karma-reporter
    reporters: ['progress'],


    // web server port
    port: 9876,


    // enable / disable colors in the output (reporters and logs)
    colors: true,


    // level of logging
    // possible values: config.LOG_DISABLE || config.LOG_ERROR || config.LOG_WARN || config.LOG_INFO || config.LOG_DEBUG
    logLevel: config.LOG_INFO,


    // enable / disable watching file and executing tests whenever any file changes
    autoWatch: false,


    // start these browsers
    // available browser launchers: https://npmjs.org/browse/keyword/karma-launcher
    browsers: ['Firefox'],


    captureTimeout: 60000,

    // Continuous Integration mode
    // if true, Karma captures browsers, runs the tests and exits
    singleRun: false
  });
};
