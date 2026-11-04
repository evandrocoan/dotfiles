// ==UserScript==
// @name         jisho add copy button to meanings-wrapper elements
// @namespace    your-namespace
// @version      1
// @description  Add a button to all elements with the class "meanings-wrapper"
// @match        *://jisho.org/*
// @grant        none
// ==/UserScript==

(function() {
    'use strict';
    function copyToClipboard(docCopy) {
        const meaningTags = docCopy.querySelectorAll('.meaning-tags');

        for (let i = 0; i < meaningTags.length; i++) {
            const tagContent = meaningTags[i].textContent;
            if (tagContent) {
                const newTag = document.createElement('span');
                newTag.style.color = 'rgb(0, 128, 0)';
                newTag.innerHTML = tagContent + ') ';
                newTag.classList = meaningTags[i].classList;
                meaningTags[i].parentNode.insertBefore(newTag, meaningTags[i]);
                meaningTags[i].parentNode.removeChild(meaningTags[i]);
            }
        }

        const meaningDefinitions = docCopy.querySelectorAll('.meaning-definition');
        for (let i = 0; i < meaningDefinitions.length; i++) {
            const meaningDefinition = meaningDefinitions[i];

            // remove `class="meaning-definition-section_divider"` and its contents
            const sectionDivider = meaningDefinition.querySelector('.meaning-definition-section_divider');
            if (sectionDivider) {
                sectionDivider.parentNode.removeChild(sectionDivider);
            }
        }

        // before the `class="supplemental_info"` and after `class="meaning-meaning` span tag closes, add `: `
        const spanElements = docCopy.querySelectorAll('span');
        for (let i = 0; i < spanElements.length; i++) {
            const spanElement = spanElements[i];
            if( !spanElement.parentNode ) {
                continue;
            }

            // remove <span class="hit">円</span> but keep the contents
            const hitElement = spanElement.querySelector('.hit');
            if(hitElement) {
                const textNode = document.createTextNode(hitElement.textContent);
                hitElement.parentNode.replaceChild(textNode, hitElement);
            }

            if (spanElement.textContent === '​') {
                const textNode = document.createTextNode(': ');
                spanElement.parentNode.replaceChild(textNode, spanElement);
            }
        }

        // replace `ul class="japanese` and its contents with new formating using `<ruby><rb>kanji</rb><rt>furigana</rt></ruby>`
        const japaneseLists = docCopy.querySelectorAll('.japanese');
        for (let i = 0; i < japaneseLists.length; i++) {
            const japaneseListItems = japaneseLists[i].querySelectorAll('li');
            for (let j = 0; j < japaneseListItems.length; j++) {
                const japaneseListItem = japaneseListItems[j];
                const kanji = japaneseListItem.querySelector('.unlinked');
                const furigana = japaneseListItem.querySelector('.furigana');
                if (kanji && furigana) {
                    const ruby = document.createElement('ruby');
                    const rt = document.createElement('rt');
                    rt.innerHTML = furigana.innerHTML;
                    if(kanji.innerHTML != kanji.textContent) {
                        throw new Error(`${kanji.innerHTML} != ${kanji.textContent}`);
                    }
                    // fix jisho bug where kanji is not separated from kana
                    let kanaList = [];
                    let kanjiList = [];
                    for (let i = 0; i < kanji.textContent.length; i++) {
                        const character = kanji.textContent.charAt(i);
                        if (/[\u3040-\u309F\u30A0-\u30FF]/g.test(character)) {
                            kanaList.push(character);
                        }
                        else {
                            kanjiList.push(character);
                        }
                    }
                    ruby.insertAdjacentHTML('beforeend', kanjiList.join(''));
                    ruby.appendChild(rt);
                    ruby.insertAdjacentHTML('beforeend', kanaList.join(''));
                    japaneseListItem.innerHTML = '';
                    japaneseListItem.appendChild(ruby);
                }
                else if(kanji) {
                    const ruby = document.createElement('ruby');
                    const rt = document.createElement('rt');
                    ruby.insertAdjacentHTML('beforeend', kanji.innerHTML)
                    ruby.appendChild(rt);
                    japaneseListItem.innerHTML = '';
                    japaneseListItem.appendChild(ruby);
                }
            }
        }

        // add `<br/>` after `class="meaning-wrapper"` contents but not if it is the last one
        const meaningWrappers = docCopy.querySelectorAll('.meaning-wrapper');
        for (let i = 0; i < meaningWrappers.length; i++) {
            const meaningWrapper = meaningWrappers[i];
            const contents = meaningWrapper.innerHTML;
            if (i < meaningWrappers.length - 1) {
                meaningWrapper.insertAdjacentElement('afterEnd', document.createElement('br'));
            }

            // remove ul and li but keep its contents
            const sentences = meaningWrapper.querySelector('.sentences');
            if(!sentences) {
                continue;
            }
            const japanese = sentences.querySelector('.japanese');
            const japaneseListItems = japanese.childNodes;
            const japaneseListItemContents = [];

            for(let i = 0; i < japaneseListItems.length; i++) {
                const japaneseListItem = japaneseListItems[i];
                if(japaneseListItem.nodeType === Node.TEXT_NODE) {
                    japaneseListItemContents.push(japaneseListItem.textContent);
                }
                else {
                    japaneseListItemContents.push(japaneseListItem.innerHTML);
                }
            };
            const newHtml = document.createElement('span');
            newHtml.innerHTML = japaneseListItemContents.join('');
            newHtml.classList = 'japanese-chars';
            japanese.parentElement.replaceChild(newHtml, japanese);
        }

        // move `class="english"` contents from inside `class="sentence"` to after it
        const sentences = docCopy.querySelectorAll('.sentence');
        for (let i = 0; i < sentences.length; i++) {
            const sentence = sentences[i];
            const english = sentence.querySelector('.english');
            if (english) {
                const englishText = english.textContent;
                sentence.removeChild(english);
                const newSpan = document.createElement('span');
                newSpan.classList.add('japanese-english');
                newSpan.textContent = englishText;
                sentence.parentNode.appendChild(newSpan);
            }
        }

        // replace all `div` tags by `span`, except the class="meaning-tags" div
        let divs = docCopy.querySelectorAll('div');
        while (divs.length > 0) {
            for (let i = 0; i < divs.length; i++) {
                const div = divs[i];
                const span = document.createElement('span');
                span.innerHTML = div.innerHTML;
                div.parentNode.replaceChild(span, div);
            }
            divs = docCopy.querySelectorAll('div');
        }

        // prefix href=/search with 'https://jisho.org/'
        const links = docCopy.querySelectorAll('[href^="/"]');
        links.forEach(function(link) {
            const href = link.getAttribute('href');
            link.setAttribute('href', 'https://jisho.org' + href);
        });

        const removeButtons = docCopy.querySelectorAll('.remove-this-button');
        removeButtons.forEach(button => {
            button.remove();
        });

        const html = docCopy.innerHTML;
        navigator.clipboard.writeText(html)
        .then(() => {
            if (Notification.permission === 'granted') {
                const notification = new Notification('HTML copied to clipboard', {
                    body: 'The HTML has been copied to the clipboard.',
                });
                setTimeout(() => {
                    notification.close();
                }, 3000);
            } else if (Notification.permission !== 'denied') {
                Notification.requestPermission().then(permission => {
                    if (permission === 'granted') {
                        const notification = new Notification('HTML copied to clipboard', {
                            body: 'The HTML has been copied to the clipboard.',
                        });
                        setTimeout(() => {
                            notification.close();
                        }, 3000);
                    }
                    else {
                        alert('Clipboard copy notification show denied');
                    }
                });
            }
        })
        .catch(err => {
            alert('Failed to copy HTML: ', err);
        });
    }

    let keepclosing = async () => {
        const meaningsWrappers = document.querySelectorAll('.meanings-wrapper:not(.remove-this-button)');
        meaningsWrappers.forEach(meaningsWrapper => {
            meaningsWrapper.classList.add('remove-this-button');
            const button = document.createElement('button');
            button.innerText = 'Copy';
            button.classList = 'remove-this-button';
            button.addEventListener('click', ()=> copyToClipboard(meaningsWrapper.cloneNode(true)));
            meaningsWrapper.appendChild(button);
        });
        setTimeout(keepclosing, 500);
    }
    setTimeout(keepclosing, 500);
})();
