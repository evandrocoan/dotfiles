// ==UserScript==
// @name         Remove genius lyrics side bars (to copy lyrics without their text)
// @namespace    *
// @version      0.1
// @description  https://webapps.stackexchange.com/questions/145612/how-to-stop-the
// @author       You
//
// @include https://genius.com/*
// @require http://code.jquery.com/jquery-3.4.1.min.js
// ==/UserScript==

(function() {
    'use strict';
    let keepclosing = async () => {
        let viewedbar = $('.RightSidebar__Container-pajcl2-0');
        if(viewedbar.length) {
            // console.log("removing running...");
            // use hide instead of remove to avoid mass flickering of the page
            viewedbar.hide();
        }
        // console.log("running");
        setTimeout(keepclosing, 500);
    }
    setTimeout(keepclosing, 500);
})();
