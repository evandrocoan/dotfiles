// ==UserScript==
// @name         Close Stackexchange Up Vote Notifications bar
// @namespace    *
// @version      0.1
// @description  https://github.com/sindresorhus/refined-github/issues/3061
// @author       You
// https://meta.stackexchange.com/questions/81379/can-we-have-a-list-of-all
// @description  https://github.com/sindresorhus/refined-github/issues/3061
// @include https://*askubuntu.com/*
// @include https://*mathoverflow.net/*
// @include https://*blogoverflow.com/*
// @include https://*serverfault.com/*
// @include https://*stackoverflow.com/*
// @include https://*stackexchange.com/*
// @include https://*stackapps.com/*
// @include https://*stackmod.blog/*
// @include https://*stackoverflow.blog/*
// @include https://*stackoverflowbusiness.com/*
// @include https://*superuser.com/*
// @include https://*tex-talk.net/*
// @include https://*thesffblog.com/*
// @require http://code.jquery.com/jquery-3.4.1.min.js
// ==/UserScript==

(function() {
    'use strict';
    let keepclosing = async () => {
        let closebutton = $('#overlay-header');
        if(closebutton.length) {
            console.log('Close Stackexchange Up Vote Notifications bar');
            closebutton.remove();
            setTimeout(keepclosing, 2000);
        }
        let begteampromotion = $('.teams-promo.overflow-hidden.z-active.bs-md.bg-black-750.fc-white.fs-body2.js-teams-promo');
        if(begteampromotion.length) {
            console.log('Close Stackexchange Team Bag Notifications bar');
            begteampromotion.remove();
        }
        let beg_banner_bookmark = $('aside[class="s-notice s-notice__success"]');
        if(beg_banner_bookmark.length) {
            console.log('Close Stackexchange Bookmark Notifications bar');
            beg_banner_bookmark.hide();
            setTimeout(keepclosing, 2000);
        }
    }
    setTimeout(keepclosing, 2000);
})();
