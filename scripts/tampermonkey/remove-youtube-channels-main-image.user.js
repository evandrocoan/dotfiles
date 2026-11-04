// ==UserScript==
// @name         Remove youtube channels main image
// @namespace    *
// @version      0.1
// @description  https://stackoverflow.com/questions/60480918/how-to-simulate-click-in-react-app-using-tampermonkey
// @author       You
//
// @include https://*youtube.com/*
// @require http://code.jquery.com/jquery-3.4.1.min.js
// ==/UserScript==

(function() {
    'use strict';

    let keepclosing = async () => {
        let menubuttons = $('tp-yt-paper-tab');

        if( menubuttons.length ) {
            let background_div = $('div[id=background]');

            if(background_div.length)
            {
                 background_div.remove();
            }

            let topbardiv = $('div[class="style-scope tp-yt-app-header"]');

            if(topbardiv.length)
            {
                topbardiv.css("padding-top", "0px");
            }

            let topbardiv2 = $('div[id="contents"]div[class="style-scope ytd-section-list-renderer"]');

            if(topbardiv2.length)
            {
                topbardiv2.css("padding-top", "50px");
                // topbardiv2.css("padding-top", "0px");
            }

            let topbardivbanner = $('div[class="banner-visible-area style-scope ytd-c4-tabbed-header-renderer"]');

            if(topbardivbanner.length)
            {
                topbardivbanner.remove();
            }

            let topbardivsize = $('div[id=header][class="style-scope ytd-browse"]');

            if(topbardivsize.length)
            {
                topbardivsize.css("height", "150px");
                // topbardivsize.css("height", "0px");
            }

            let topbardivjoinbar = $('ytd-recognition-shelf-renderer[class="style-scope ytd-item-section-renderer"]');

            if(topbardivjoinbar.length)
            {
                topbardivjoinbar.hide();
            }

            let topghostdiv = $('div[id=contentContainer][class="style-scope tp-yt-app-header-layout"]');

            if(topghostdiv.length)
            {
                topghostdiv.hide();
            }

            // Unpin the main big bar (by putting it inside the main body)
            // use 5 seconds to avoid delay to avoid unfocusing the search button type field each second
            //if( $('div[id="contents"]div[class="style-scope ytd-section-list-renderer"] > div[class="style-scope tp-yt-app-header"]').length < 0 ) {
            //}
        }

        setTimeout(keepclosing, 5000);
    }
    setTimeout(keepclosing, 5000);
})();
