// ==UserScript==
// @name         Always click youtube show more (channels button)
// @namespace    *
// @version      0.1
// @description  https://stackoverflow.com/questions/60480918/how-to-simulate-click-in-react-app-using-tampermonkey
// @author       You
//
// @include https://*youtube.com/*
// @exclude https://*youtube.com/*/TucaLoretti/*
// @exclude https://*youtube.com/*/UC1__NTyvkBZElGBK1qmtoMg/*
// @require http://code.jquery.com/jquery-3.4.1.min.js
// ==/UserScript==

(function() {
    'use strict';
    let showmoreregex = new RegExp("Show \\d+ more"); // expression here

    let keepclosing = async () => {

        let showmorebutton = $('yt-formatted-string[class="title style-scope ytd-guide-entry-renderer"]').filter(function () {
            return showmoreregex.test($(this).text());
        });

        // console.log(`showmorebutton ${showmorebutton.text()}`);
        if( showmorebutton.length ) {
            showmorebutton[0].click();
            showmorebutton.remove();
        }

        setTimeout(keepclosing, 1000);
    }
    setTimeout(keepclosing, 1000);
})();
