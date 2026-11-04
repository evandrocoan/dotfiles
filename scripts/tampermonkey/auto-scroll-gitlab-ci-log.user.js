// ==UserScript==
// @name         Auto scroll gitlab ci log
// @namespace    *
// @version      0.1
// @description  ...
// @author       Evandro Coan
//
// @include http*://gitlab*
//
// @require http://code.jquery.com/jquery-3.4.1.min.js
// ==/UserScript==
//
// https://gitlab.com/gitlab-org/gitlab/-/issues/37313 - Job Log Page is no longer auto scrolling to the bottom
// https://stackoverflow.com/questions/3898130/check-if-a-user-has-scrolled-to-the-bottom/3898152
//
(function() {
    'use strict';
        function getDocHeight() {
        var D = document;
        return Math.max(
            D.body.scrollHeight, D.documentElement.scrollHeight,
            D.body.offsetHeight, D.documentElement.offsetHeight,
            D.body.clientHeight, D.documentElement.clientHeight
        );
    }
    setInterval(function(){
            if($(window).scrollTop() + $(window).height() > getDocHeight() - 300) {
                $('button[data-testid="job-controller-scroll-bottom"]').click();
            }
        },
        1000);
})();
