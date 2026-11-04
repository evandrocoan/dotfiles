// ==UserScript==
// @name         Close Lastfm player bar
// @namespace    *
// @version      0.1
// @description  https://github.com/sindresorhus/refined-github/issues/3061
// @author       You
// https://meta.stackexchange.com/questions/81379/can-we-have-a-list-of-all
// @include https://*last.fm/*
// @require http://code.jquery.com/jquery-3.4.1.min.js
// ==/UserScript==

let things = `
// https://stackoverflow.com/questions/7474354/include-jquery-in-the-javascript-console
var jq = document.createElement('script');
jq.src = "https://cdnjs.cloudflare.com/ajax/libs/jquery/3.3.1/jquery.min.js";
document.getElementsByTagName('head')[0].appendChild(jq);
// ... give time for script to load, then type (or see below for non wait option)
jQuery.noConflict();
`;

(function() {
    'use strict';
    deleteElement('div[data-more-string="More…"].navlist.navlist--more.masthead-nav.hidden-xs');
    deleteElement('.masthead-logo');
    deleteElement('.top-bar');
    function deleteElement(selector) {
        let delayed = () => {
            // Avoid reprocessing when on background/not focused
            if (document.hasFocus()) {
                // console.log('Tab is active');
            }
            else {
                // console.log('Tab is not active');
                setTimeout(delayed, 1000);
                return;
            }

            let element = $(String(selector));
            if(element.length) {
                console.log(`Deleting element '${element.text().replace(/\s+/g, ' ').trim()}' button`);
                element.remove();
            }
            setTimeout(delayed, 2000);
        }
        setTimeout(delayed, 200);
    }

    $('#content').css({'padding-top': '0px'});
    if( String(window.location.href).toLowerCase().includes('ironhead4life') ) {
        setTimeout(fixScrobleLink, 1000);
    }
    function fixScrobleLink() {
        // Avoid reprocessing when on background/not focused
        if (document.hasFocus()) {
            // console.log('Tab is active');
        }
        else {
            // console.log('Tab is not active');
            setTimeout(fixScrobleLink, 1000);
            return;
        }

        $('.chartlist-name>a').each(function(index, item) {
            // console.log(index)
            let newitem = $(item).attr('href');

            if( ! String(newitem).includes('IronHead4Life') ) {
                let newitemsrc = String(newitem).replace('/music/', '/user/IronHead4Life/library/music/');

                // console.log(newitemsrc);
                $(item).attr('href', newitemsrc);
                $(item).attr ('target', '_blank');
            }
        });
        setTimeout(fixScrobleLink, 1000);
    }
})();
