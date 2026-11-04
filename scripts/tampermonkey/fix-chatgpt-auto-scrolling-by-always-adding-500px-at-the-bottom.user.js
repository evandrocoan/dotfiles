// ==UserScript==
// @name         Fix chatgpt auto-scrolling by always adding 500px at the bottom
// @namespace    http://tampermonkey.net/
// @version      0.1
// @description  Modify the height of the last HTML element with a data-testid attribute
// @author       You
// @match        https://chat.openai.com/*
// @grant        none
// ==/UserScript==

(function() {
    'use strict';
    function setElementHeight() {
        //let elements = document.querySelectorAll('[data-role="assistant"]');  // use for superpower chatgpt chrome extension
        let elements = document.querySelectorAll('[data-testid^="conversation-turn"]');  // use for chatgpt vanilla

        let heightJump = 500;
        let jumpTimeoutInSeconds = 30;
        let lastElement = elements[elements.length - 1];

        if (lastElement)
        {
            let height = lastElement.scrollHeight || -1;
            let setMinHeight = parseInt(lastElement.style.minHeight, 10) || -1;

            let lastHeight = parseInt(lastElement.getAttribute("data-last-scrool"), 10) || height;
            let lastHeightCount = parseInt(lastElement.getAttribute("data-last-scrool-count"), 10) || 0;

            // console.log(`height ${height}, lastHeight ${lastHeight}, setMinHeight ${setMinHeight}, lastHeightCount ${lastHeightCount}.`)
            if (height > lastHeight) {
                height += heightJump;
                lastElement.style.minHeight = `${height}px`;
            }

            if( height == lastHeight )
            {
                if(lastHeightCount > jumpTimeoutInSeconds) {
                    // console.log(`Reseting height ${height} ${lastHeightCount}.`)
                    lastElement.style.minHeight = `auto`;
                }
                lastHeightCount += 1;
            }
            else {
                lastHeightCount = 0;
            }

            lastElement.setAttribute("data-last-scrool", height);
            lastElement.setAttribute("data-last-scrool-count", lastHeightCount);
        }

        let penultiLastElement = elements[elements.length - 2];
        let penultiLastElement2 = elements[elements.length - 3];

        if (penultiLastElement) {
            penultiLastElement.style.minHeight = `auto`;
        }
        if (penultiLastElement2) {
            penultiLastElement2.style.minHeight = `auto`;
        }

        let chatTypeHeaders = document.querySelectorAll('header.sticky.top-0');
        if(chatTypeHeaders) {
            chatTypeHeaders.forEach((chatTypeHeader) => {
                chatTypeHeader.className = "";
            });
        }
    }

    setInterval(setElementHeight, 1000);
})();
