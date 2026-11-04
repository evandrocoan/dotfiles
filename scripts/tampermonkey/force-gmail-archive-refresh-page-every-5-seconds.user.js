// ==UserScript==
// @name         Force GMail Archive refresh page every 5 seconds
// @namespace    *
// @version      0.1
// @description  This is because on Linux the page some times takes long time to refresh
// @author       Evandro Coan
//
// @include https://mail.google.com/*
// @require http://code.jquery.com/jquery-3.4.1.min.js
// ==/UserScript==

(function() {
    'use strict';
    let keepclosing = async () => {
        let viewedbar = $('div[aria-label="Refresh"]');

        if(viewedbar.length)
        {
            console.log('Clicking refresh');
            viewedbar.click();
        }
        else {
            console.log(viewedbar);
        }
    }
    setInterval(keepclosing, 5000);
})();
