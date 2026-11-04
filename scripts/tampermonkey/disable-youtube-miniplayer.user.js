// ==UserScript==
// @name         Disable YouTube Miniplayer
// @author       u/IStoleThePies
// @include      *youtube.com*
// @license     MIT
// ==/UserScript==

(function() {
    document.body.addEventListener("yt-navigate-finish", function(event) {
        if (document.getElementsByTagName('ytd-miniplayer').length && document.querySelector('ytd-miniplayer') && document.querySelector('ytd-miniplayer').parentNode) {
            document.querySelector('ytd-miniplayer').parentNode.removeChild(document.querySelector('ytd-miniplayer'));
        }
        if (document.getElementsByClassName('ytp-miniplayer-button').length && document.querySelector('.ytp-miniplayer-button') && document.querySelector('.ytp-miniplayer-button').parentNode) {
            document.querySelector('.ytp-miniplayer-button').parentNode.removeChild(document.querySelector('.ytp-miniplayer-button'))
        }
        if (window.location.pathname != "/watch" && document.querySelector('#movie_player video') && document.querySelector('#movie_player video').parentNode) {
            document.querySelector('#movie_player video').parentNode.removeChild(document.querySelector('#movie_player video'));
        }
    });
})();
