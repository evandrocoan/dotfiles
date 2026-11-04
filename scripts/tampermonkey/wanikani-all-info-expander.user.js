// ==UserScript==
// @name         WaniKani All Info Expander
// @namespace    http://www.wanikani.com
// @version      0.2.1
// @description  Automatically click "Show All Information"
// @author       polv
// @match        https://www.wanikani.com/extra_study/session*
// @match        https://www.wanikani.com/review/session*
// @match        https://www.wanikani.com/subjects/*
// @match        https://www.wanikani.com/subject-lessons/*
// @match        https://preview.wanikani.com/extra_study/session*
// @match        https://preview.wanikani.com/review/session*
// @match        https://preview.wanikani.com/subjects*
// @icon         https://www.google.com/s2/favicons?sz=64&domain=wanikani.com
// @license      MIT
// @homepage     https://github.com/patarapolw/wanikani-userscript/blob/master/userscripts/all-info.user.js
// @grant        none
// ==/UserScript==

// @ts-check
(function () {
  'use strict';

  /** @type {'meaning' | 'reading' | ''} question type */
  let qType = '';
  /** @type {'Vocabulary' | 'Radical' | 'Kanji' | ''} subject type  */
  let sType = '';

  const inputObserver = new MutationObserver((muts) => {
    // if (qType !== 'meaning') return;

    setTimeout(() => {
      for (const m of muts) {
        const target = /** @type {HTMLDivElement} */ (m.target);
        /**
         * @type {'true' | 'false'}
         * whether it is answered correctly. Must be non-empty string.
         */
        const attrCorrect = /** @type {'true' | 'false'} */ (
          target.getAttribute('correct')
        );

        if (attrCorrect) {
          const btn = document.querySelector(
            '.additional-content__item--item-info',
          );
          if (btn && !btn.className.includes('--open')) {
            // @ts-ignore
            btn.click();
          }
          return;
        }
      }
    }, 100);
  });

  /** @type {Element | null} */
  let inputContainer = null;

  window.addEventListener('willShowNextQuestion', (e) => {
    qType = '';

    if ('detail' in e) {
      const { subject, questionType } = /** @type {any} */ (e.detail);
      qType = questionType;
      sType = subject.type;
    }

    const newInput = document.querySelector('.quiz-input__input-container');
    if (newInput && newInput !== inputContainer) {
      inputContainer = newInput;
      inputObserver.observe(newInput, {
        attributes: true,
        attributeFilter: ['correct'],
      });
    }
  });
})();
