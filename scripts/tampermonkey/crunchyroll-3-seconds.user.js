// ==UserScript==
// @name         Crunchyroll 3 Seconds
// @namespace    http://tampermonkey.net/
// @version      1.3
// @description  Makes arrow keys skip 3s, removes focus, and handles held keys for slow PCs
// @author       You
// @match        *://*.crunchyroll.com/*
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    // Variable to store the last time the skip was executed
    let lastExecutionTime = 0;

    window.addEventListener('keydown', function(e) {
        // Check if the pressed key was the Right Arrow or Left Arrow
        if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {

            // Look for the video player on the page
            const video = document.querySelector('video');

            if (video) {
                // Remove focus from any selected element (like the progress bar)
                if (document.activeElement) {
                    document.activeElement.blur();
                }

                // This blocks Crunchyroll's original code from running (cancels the 10 seconds)
                e.stopImmediatePropagation();
                e.preventDefault();

                const now = Date.now();

                // Check if the key is being held down
                if (e.repeat) {
                    // Throttle: only allow the skip to happen once every 300 milliseconds
                    // This prevents the browser from freezing on slow computers
                    if (now - lastExecutionTime < 300) {
                        return;
                    }

                    // When holding the key, skip 15 seconds
                    if (e.key === 'ArrowRight') {
                        video.currentTime += 15;
                    } else if (e.key === 'ArrowLeft') {
                        video.currentTime -= 15;
                    }
                } else {
                    // Normal single press: skip 3 seconds
                    if (e.key === 'ArrowRight') {
                        video.currentTime += 3;
                    } else if (e.key === 'ArrowLeft') {
                        video.currentTime -= 3;
                    }
                }

                // Update the last execution time
                lastExecutionTime = now;
            }
        }
    }, true); // The 'true' ensures this script runs BEFORE Crunchyroll's script
})();
