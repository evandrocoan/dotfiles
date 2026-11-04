// ==UserScript==
// @name         Click "Mostrar mais comentários"
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  Automatically clicks on the "Mostrar mais comentários" button when it appears.
// @author       Your Name
// @match        *://some/page
// @grant        none
// ==/UserScript==

(function () {
    'use strict';

    function clickMostrarMaisComentarios() {
        const button = [...document.querySelectorAll('button')].find(
            btn => btn.textContent.trim() === "Mostrar mais comentários"
        );

        if (button) {
            console.log("Found the button! Clicking...");
            button.click();
        }
    }

    setInterval(clickMostrarMaisComentarios, 500);
})();
