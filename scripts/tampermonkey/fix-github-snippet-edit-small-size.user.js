// ==UserScript==
// @name         Fix GitHub snippet edit small size
// @namespace    http://tampermonkey.net/
// @version      0.1
// @description  try to take over the world!
// @author       You
// @match        https://gist.github.com/evandrocoan/*
// @require http://code.jquery.com/jquery-3.4.1.min.js
// ==/UserScript==

(function() {
    'use strict';
    let keepclosing = async () => {
        let viewedbar = $('div[class="CodeMirror cm-s-github-light CodeMirror-wrap"]').not('span[data-donot-process-this-again]');

        // console.log('running');
        // console.log(viewedbar);
        if(viewedbar.length)
        {
            viewedbar.css("height", "700px");
            viewedbar.attr('data-donot-process-this-again', true);
        }
        setTimeout(keepclosing, 500);
    }
    setTimeout(keepclosing, 500);
})();
