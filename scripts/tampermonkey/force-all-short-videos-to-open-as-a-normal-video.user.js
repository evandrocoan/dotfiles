// ==UserScript==
// @name         Force all short videos to open as a normal video!
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
        let viewedbar = $('a[href*="/shorts"]');

        // console.log('running');
        // console.log(viewedbar);
        if(viewedbar.length)
        {
            $(viewedbar).each(function(index, item)
            {
                // console.log(index)
                let newitem = $(item).attr('href');
                let newitemsrc = String(newitem).replace('/shorts/', '/watch?v=');

                // console.log(newitemsrc);
                $(item).attr('rel', `noopener noreferrer`);
                //$(item).attr('target', `_blank`);
                $(item).attr('onclick', `
                    if( '${newitemsrc}' !=  this.getAttribute('href')) return;
                    window.open('${newitemsrc}', '');
                    setTimeout(function(){ history.back(); }, 500);
                    return false;
                `);
                $(item).removeAttr('href');
                $(item).attr('href', newitemsrc);
                //$(item).attr('data-saferedirecturl', newitemsrc);
            })
        }
        setTimeout(keepclosing, 500);
    }
    setTimeout(keepclosing, 500);
})();








