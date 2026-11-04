// ==UserScript==
// @name         Close GitHub Notifications bar
// @namespace    *
// @version      0.1
// @description  https://github.com/sindresorhus/refined-github/issues/3061
//               https://gist.github.com/evandrocoan/0e25dd233f3f99352a8147041809ba8d
//
// @author       You
// @include http://*github.com/*
// @include https://*github.com/*
// @require http://code.jquery.com/jquery-3.4.1.min.js
// ==/UserScript==

(function() {
    'use strict';
    clickButton('button[aria-label="Close notification controls"].js-flash-close');
    deleteElement('.js-sticky.js-sticky-offset-scroll.top-0.gh-header-sticky.is-stuck');

    // http://en.enisozgen.com/hide-github-academic-discount-coupon-error/
    deleteElement('.flash.flash-full.js-notice.flash-error');

    function deleteElement(selector) {
        let delayed = () => {
            let element = $(String(selector));
            if(element.length) {
                console.log(`Deleting '${element.text().replace(/\s+/g, ' ').trim()}' button`);
                element.remove();
            }
            setTimeout(delayed, 2000);
        }
        setTimeout(delayed, 2000);
    }
    function clickButton(selector) {
        let delayed = () => {
            let element = $(String(selector));
            if(element.length) {
                console.log(`Closing element '${element.html()}' button`);
                element.click();
            }
            setTimeout(delayed, 2000);
        }
        setTimeout(delayed, 2000);
    }
})();
