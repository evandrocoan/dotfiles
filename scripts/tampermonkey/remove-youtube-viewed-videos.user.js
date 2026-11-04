// ==UserScript==
// @name         Remove youtube viewed videos
// @namespace    *
// @version      0.1
// @description  https://webapps.stackexchange.com/questions/145612/how-to-stop-the
// @author       You
//
// @include https://*youtube.com/*
// @require http://code.jquery.com/jquery-3.4.1.min.js
// ==/UserScript==

(function() {
    'use strict';
    let keepclosing = async () => {
        let viewedbar = $('.style-scope.ytd-thumbnail-overlay-resume-playback-renderer');
        if(viewedbar.length) {
            // console.log("removing running...");
            let parent = viewedbar.closest('.style-scope.ytd-rich-grid-renderer');
            if(parent.length) {
                // use hide instead of remove to avoid mass flickering of the page
                parent.hide();
            }
        }
        // console.log("running");
        setTimeout(keepclosing, 500);
    }
    setTimeout(keepclosing, 500);
})();
