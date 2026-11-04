// ==UserScript==
// @name         Move weather.com real feel temperature side-by-side with temperature
// @namespace    http://tampermonkey.net/
// @version      2024-01-10
// @description  try to take over the world!
// @author       You
// @match        https://weather.com/weather/hourbyhour/*
// @icon         https://www.google.com/s2/favicons?sz=64&domain=weather.com
// @require http://code.jquery.com/jquery-3.4.1.min.js
// @grant        none
// ==/UserScript==

(function() {
    'use strict';
    setInterval(function(){
        let temperatures = $('span[data-testid="TemperatureValue"]');
        if( temperatures.length && temperatures[0].textContent.includes('/') ) {
            temperatures = temperatures.not('span[data-donot-process-this-again]');
        }

        for (let index = 0; index < temperatures.length; index+=2) {
            let main_temperature = $(temperatures[index]);
            let real_feel = $(temperatures[index+1]);
            main_temperature.append(` / ${real_feel.text()}`)

            real_feel.attr('data-donot-process-this-again', true);
            main_temperature.attr('data-donot-process-this-again', true);
        }

        let percentages = $('span[data-testid="PercentageValue"]').not('span[data-donot-process-this-again]');

        for (let index = 0; index < percentages.length; index+=3) {
            let rain_probability = $(percentages[index]);
            let humidity_percentage = $(percentages[index+1]);
            let cloud_clover = $(percentages[index+2]);
            rain_probability.append(`&nbsp;${humidity_percentage.text()}&nbsp;${cloud_clover.text()}`)

            rain_probability.attr('data-donot-process-this-again', true);
            humidity_percentage.attr('data-donot-process-this-again', true);
            cloud_clover.attr('data-donot-process-this-again', true);
        }
    },
    1000);
})();
