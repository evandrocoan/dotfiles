// ==UserScript==
// @name         Remove youtube channels logo and always show all videos
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

    let keepclosing = async () => {
        let menubuttons = $('tp-yt-paper-tab');

        if( menubuttons.length ) {
            // console.log("removing running...");
            let videosButton = menubuttons[1];
            let ariaSelected = $(videosButton).attr('aria-selected');

            // console.log(`ariaSelected ${ariaSelected}`);
            if( ariaSelected == 'false' ) {
                menubuttons[1].click();
            }

            // delete youtube useless top bar/logo
            let topbar = $('.style-scope.ytd-c4-tabbed-header-renderer');
            if(topbar.length) {
                 topbar.hide();
            }
        }

        setTimeout(keepclosing, 1000);
    }
    setTimeout(keepclosing, 1000);
})();
