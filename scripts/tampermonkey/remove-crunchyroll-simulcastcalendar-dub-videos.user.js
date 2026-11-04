// ==UserScript==
// @name         Remove crunchyroll simulcastcalendar dub videos
// @namespace    *
// @version      0.1
// @description  https://webapps.stackexchange.com/questions/145612/how-to-stop-the
// @author       You
//
// @include https://*crunchyroll*/simulcastcalendar*
// @require http://code.jquery.com/jquery-3.4.1.min.js
// ==/UserScript==

(function() {
    'use strict';
    let keepclosing = async () => {
        let viewedbar = $('cite:contains(" Dub)")');
        if(viewedbar.length) {
            // console.log("removing running...");
            let parent = viewedbar.closest('li');
            if(parent.length) {
                // use hide instead of remove to avoid mass flickering of the page
                parent.hide();
            }
        }
        // console.log("running");
        // setTimeout(keepclosing, 500);
    }
    setTimeout(keepclosing, 1500);
})();
