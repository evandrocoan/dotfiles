// ==UserScript==
// @name         Remove Specific Paragraph from Page
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  Remove paragraph containing specific text
// @author       Your Name
// @match        *://some/page
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    function removeParagraphs() {
        const paragraphs = document.querySelectorAll('p');

        paragraphs.forEach(paragraph => {
            if (paragraph.textContent.includes('some text')) {
                paragraph.remove();
            }
        });
    }

    setInterval(removeParagraphs, 500);
})();
