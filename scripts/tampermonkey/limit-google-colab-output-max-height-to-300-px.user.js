// ==UserScript==
// @name         Limit google colab output max height to 300 px
// @namespace    http://tampermonkey.net/
// @version      2025-02-03
// @description  Limit google colab output max height to 300 px
// @author       You
// @match        https://colab.research.google.com/drive/**
// @grant        none
// ==/UserScript==

(function() {
    'use strict';
    function runContinually() {
        const elements = document.querySelectorAll('.output-content:not(.alreadyprocessed)');

        elements.forEach(element => {
            element.style.maxHeight = '300px';
            element.classList.add('alreadyprocessed');
        });
    }

    setInterval(runContinually, 500);
})();
