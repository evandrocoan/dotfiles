// ==UserScript==
// @name         Force GMail Archive button to go to back after clicking on it
// @namespace    *
// @version      0.1
// @description  Force GMail Archive button to go to back after clicking on it
// @author       Evandro Coan
//
// @include https://mail.google.com/*
// @require http://code.jquery.com/jquery-3.4.1.min.js
// ==/UserScript==
(function() {
    'use strict';
    let keepclosing = async () => {
        let viewedbar = $('div[data-tooltip="Archive"][tabindex="0"]').not('span[data-donot-process-this-again]');
        // console.log('running');
        // console.log(viewedbar);
        if(viewedbar.length)
        {
            let previousItem = function() {
                // let viewedbar = $('div[data-tooltip][tabindex="0"][role="button"]').filter(function() {
                //     return $(this).attr('data-tooltip').match(/.*Back.*/);
                // });
                let viewedbar = $('div[data-tooltip="All Mail"]');
                if(viewedbar.length) {
                    viewedbar.click();
                }
                return false;
            };
            viewedbar.on('click', previousItem);
            viewedbar.attr('data-donot-process-this-again', true);
        }
        setTimeout(keepclosing, 500);
    }
    setTimeout(keepclosing, 500);

    let keepopening = async () => {
        let expandbutton = $('div[data-tooltip="Show trimmed content"][aria-expanded="false"]');

        setTimeout(keepopening, 500);
        if( expandbutton.length ) {
            expandbutton.click();
        }
    }
    setTimeout(keepopening, 500);

    let keepremovingsearchbar = async () => {
        let expandbutton = $('div[aria-label="search refinement"]');
        let divsizetofix = $('div[gh="tm"]');

        setTimeout(keepremovingsearchbar, 500);
        divsizetofix.css("height", "30px");
        expandbutton.remove();
    }
    setTimeout(keepremovingsearchbar, 500);
})();
