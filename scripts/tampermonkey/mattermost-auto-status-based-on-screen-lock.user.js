// ==UserScript==
// @name         Mattermost Auto Status Based on Screen Lock
// @namespace    http://tampermonkey.net/
// @version      1.2
// @description  Report Mattermost notifications to the local tray and update presence on screen lock
// @author       You
// @match        http://mattermost.khomp.corp/*
// @match        https://mattermost.khomp.corp/*
// @icon         https://www.google.com/s2/favicons?sz=64&domain=mattermost.com
// @grant        GM_xmlhttpRequest
// @connect      127.0.0.1
// @connect      localhost
// @connect      mattermost.khomp.corp
// @run-at       document-start
// ==/UserScript==

(function() {
    'use strict';

    const SCREEN_STATUS_URL = 'http://127.0.0.1:8000/screen-status';
    const CHECK_INTERVAL = 5000; // Check every 5 seconds
    const NOTIFICATIONS_URL = 'http://127.0.0.1:8000/mattermost/notifications';
    const source = Array.from(crypto.getRandomValues(new Uint32Array(4)),
        value => value.toString(16).padStart(8, '0')).join('');
    let sequence = 0;
    let reporting = false;
    let pendingReport = false;
    let leaving = false;
    let reportTimer = null;
    const faviconPixels = new Map();
    const faviconStates = new Map();
    const pendingFavicons = new Set();
    let lastDetection = null;

    function readFaviconPixels(href) {
        if (!faviconPixels.has(href)) {
            const promise = new Promise((resolve, reject) => {
                const image = new Image();
                const timer = setTimeout(() => finish(new Error('Favicon load timed out')), 5000);
                const finish = (error, pixels) => {
                    clearTimeout(timer);
                    image.onload = image.onerror = null;
                    if (error) reject(error);
                    else resolve(pixels);
                };
                image.onload = () => {
                    try {
                        const width = image.naturalWidth;
                        const height = image.naturalHeight;
                        if (width !== height || ![16, 24, 32, 64, 96].includes(width)) {
                            throw new Error('Unsupported favicon dimensions');
                        }
                        const canvas = document.createElement('canvas');
                        canvas.width = width;
                        canvas.height = height;
                        const context = canvas.getContext('2d');
                        context.drawImage(image, 0, 0);
                        finish(null, {width, data: context.getImageData(0, 0, width, height).data});
                    } catch (error) {
                        finish(error);
                    }
                };
                image.onerror = () => finish(new Error('Favicon could not be loaded'));
                image.src = href;
            });
            faviconPixels.set(href, promise);
            promise.catch(() => faviconPixels.delete(href));
        }
        return faviconPixels.get(href);
    }

    async function identifyHashedFavicon(url, staticPath) {
        const actual = await readFaviconPixels(url.href);
        const states = ['default', 'unread', 'mentions'];
        const references = await Promise.all(states.map(state => readFaviconPixels(
            new URL(`${staticPath}images/favicon/favicon-${state}-${actual.width}x${actual.width}.png`, url.origin).href
        )));
        return states.find((state, index) => {
            const reference = references[index];
            return actual.width === reference.width && actual.data.length === reference.data.length &&
                actual.data.every((value, offset) => value === reference.data[offset]);
        });
    }

    function faviconState(href) {
        const url = new URL(href, window.location.href);
        const named = url.pathname.match(/\/favicon-(default|unread|mentions)-\d+x\d+(?:\.[a-f0-9]+)?\.png$/i)?.[1];
        if (named) return named.toLowerCase();
        if (faviconStates.has(url.href)) return faviconStates.get(url.href);

        // Webpack emits optimized icons as /static/files/<contenthash>.png.
        // Match decoded pixels against the copied originals, which retain their names.
        // Restrict image reads to Mattermost's own static assets; nothing is uploaded.
        const hashed = url.pathname.match(/^(.*\/static\/)files\/[a-f0-9]+\.png$/i);
        if (url.origin === window.location.origin && hashed && !pendingFavicons.has(url.href)) {
            pendingFavicons.add(url.href);
            identifyHashedFavicon(url, hashed[1]).then(state => {
                faviconStates.set(url.href, state);
                if (state) scheduleReport();
            }).catch(() => {
                // A later heartbeat retries failed image loads, without a tight retry loop.
            }).finally(() => pendingFavicons.delete(url.href));
        }
        return undefined;
    }

    // Mirror Mattermost's own aggregate favicon, including its mute/thread rules.
    // Unknown/login/loading pages must never report confirmed absence of activity.
    function notificationState() {
        if (leaving || !document.querySelector('#channel_view')) {
            return 'unknown';
        }
        const states = Array.from(document.querySelectorAll('link[rel~="icon"]'), link => faviconState(link.href));
        if (states.includes('mentions')) return 'mention';
        if (states.includes('unread')) return 'unread';
        if (states.length && states.every(state => state === 'default')) return 'idle';
        return 'unknown';
    }

    function reportNotifications() {
        if (reporting) {
            pendingReport = true;
            return;
        }
        reporting = true;
        pendingReport = false;
        const state = notificationState();
        const detection = state === 'unknown' ?
            (leaving || !document.querySelector('#channel_view') ? 'channel view unavailable' : 'favicon not recognized yet') : state;
        if (detection !== lastDetection) {
            console.info('Mattermost tray:', detection);
            lastDetection = detection;
        }
        const finish = () => {
            reporting = false;
            if (pendingReport) reportNotifications();
        };
        GM_xmlhttpRequest({
            method: 'POST',
            url: NOTIFICATIONS_URL,
            anonymous: true,
            timeout: 5000,
            headers: {'Content-Type': 'application/json', 'X-Mattermost-Tray': '1'},
            data: JSON.stringify({source, sequence: ++sequence, state}),
            onload: finish,
            onerror: finish,
            ontimeout: finish,
            onabort: finish
        });
    }

    function scheduleReport() {
        clearTimeout(reportTimer);
        reportTimer = setTimeout(reportNotifications, 150);
    }

    function startNotificationReports() {
        const observer = new MutationObserver(scheduleReport);
        observer.observe(document.head, {
            subtree: true, childList: true, attributes: true,
            attributeFilter: ['href', 'rel', 'sizes']
        });
        setInterval(reportNotifications, 15000);
        window.addEventListener('pagehide', () => {
            leaving = true;
            reportNotifications();
        });
        window.addEventListener('pageshow', () => {
            leaving = false;
            reportNotifications();
        });
        document.addEventListener('visibilitychange', reportNotifications);
        reportNotifications();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', startNotificationReports, {once: true});
    } else {
        startNotificationReports();
    }

    let lastStatus = null;
    let mattermostWindow = null;

    // Function to check screen lock status
    function checkScreenStatus() {
        GM_xmlhttpRequest({
            method: 'GET',
            url: SCREEN_STATUS_URL,
            timeout: 5000,
            onload: function(response) {
                if (response.status !== 200) return;
                try {
                    const data = JSON.parse(response.responseText);
                    if (!['locked', 'blank', 'unlocked'].includes(data.status)) return;
                    handleScreenStatus(data);
                } catch (error) {
                    console.error('Error parsing screen status:', error);
                }
            },
            onerror: function(error) {
                console.error('Error checking screen status:', error);
            }
        });
    }

    // Function to handle screen status changes
    function handleScreenStatus(data) {
        // console.log('handleScreenStatus called with data:', data, 'lastStatus:', lastStatus);

        if (data.status === lastStatus) {
            // console.log('Status unchanged, skipping update. Full data:', data);
            return; // No change, do nothing
        }

        console.log(`Screen status changed: ${lastStatus} -> ${data.status}`);
        console.log('Full data:', data);
        lastStatus = data.status;

        // Check if it's off-hours (after 21:00, before 8:00, or weekend)
        const now = new Date();
        const hour = now.getHours();
        const day = now.getDay(); // 0 = Sunday, 6 = Saturday
        const isWeekend = (day === 0 || day === 6);
        const isOffHours = hour >= 21 || hour < 7;

        if (isWeekend || isOffHours) {
            console.log(`Off-hours detected (hour: ${hour}, day: ${day}). Setting status to offline.`);
            setMattermostStatus('offline');
        } else if (data.status === 'locked') {
            setMattermostStatus('offline');
        } else if (data.status === 'blank') {
            setMattermostStatus('dnd'); // dnd = Do Not Disturb (busy)
        } else if (data.status === 'unlocked') {
            setMattermostStatus('online');
        }
    }

    // Function to set Mattermost status
    function setMattermostStatus(status) {
        // Try to find Mattermost in current window
        if (window.location.href.includes('mattermost')) {
            setStatusInCurrentWindow(status);
        }
    }

    // Function to set status in current Mattermost window
    function setStatusInCurrentWindow(status) {
        console.log(`Setting Mattermost status to: ${status}`);

        // Wait for page to load
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                setTimeout(() => setStatusViaUI(status), 2000);
            });
        } else {
            setTimeout(() => setStatusViaUI(status), 2000);
        }
    }

    // Function to set status via UI manipulation
    function setStatusViaUI(status) {
        // Method 1: Try to use Mattermost API if available
        if (window.WebappUtils || window.store) {
            try {
                // Try to access Redux store (Mattermost uses Redux)
                const store = window.store;
                if (store && store.dispatch) {
                    console.log('Using Mattermost store to set status');
                    // This would require importing Mattermost actions
                    // For now, we'll use the UI method
                }
            } catch (e) {
                console.log('Store method not available, using UI method');
            }
        }

        // Method 2: Simulate clicking the status menu
        try {
            // Find the user menu button (this selector may need adjustment based on your Mattermost version)
            const userMenuButton = document.querySelector('[aria-label="user menu"], [aria-label="profile"], button[aria-label*="status"]');

            if (userMenuButton) {
                userMenuButton.click();

                setTimeout(() => {
                    // Find and click the appropriate status option
                    const statusButtons = document.querySelectorAll('[role="menuitem"], .MenuItem');

                    for (const button of statusButtons) {
                        const buttonText = button.textContent.toLowerCase();
                        if ((status === 'offline' && buttonText.includes('offline')) ||
                            (status === 'online' && buttonText.includes('online'))) {
                            console.log(`Clicking status button: ${buttonText}`);
                            button.click();
                            break;
                        }
                    }

                    // Close the menu by clicking elsewhere
                    setTimeout(() => {
                        document.body.click();
                    }, 500);
                }, 500);
            }
        } catch (error) {
            console.error('Error setting status via UI:', error);
        }

        // Method 3: Try API call directly
        tryApiStatusUpdate(status);
    }

    // Function to try direct API update
    function tryApiStatusUpdate(status) {
        // First, get the current user ID
        fetch(window.location.origin + '/api/v4/users/me')
            .then(response => response.json())
            .then(userData => {
                const userId = userData.id;
                const mattermostApiUrl = window.location.origin + '/api/v4/users/me/status';

                // Get CSRF token from cookie
                const csrfToken = document.cookie.split('; ').find(row => row.startsWith('MMCSRF='))?.split('=')[1];

                const headers = {
                    'Content-Type': 'application/json',
                };

                // Add CSRF token if available
                if (csrfToken) {
                    headers['X-CSRF-Token'] = csrfToken;
                    headers['X-Requested-With'] = 'XMLHttpRequest';
                }

                GM_xmlhttpRequest({
                    method: 'PUT',
                    url: mattermostApiUrl,
                    headers: headers,
                    data: JSON.stringify({
                        user_id: userId,
                        status: status
                    }),
                    onload: function(response) {
                        if (response.status === 200) {
                            console.log(`✓ Successfully set Mattermost status to ${status} via API`);
                        } else if (response.status === 401) {
                            console.log('✗ API authentication failed - UI method will be used as fallback');
                        } else if (response.status === 400) {
                            console.log('✗ API bad request (400) - UI method will be used as fallback');
                            console.log('Response:', response.responseText);
                        } else {
                            console.log(`API status update returned: ${response.status}`);
                        }
                    },
                    onerror: function(error) {
                        console.log('API status update failed:', error);
                    }
                });
            })
            .catch(error => {
                console.log('Could not get user ID, UI method will be used');
            });
    }

    // Only run on Mattermost pages
    if (window.location.href.includes('mattermost') ||
        window.location.hostname.includes('mattermost')) {
        console.log('Mattermost Auto Status Script loaded');

        // Start checking screen status
        setInterval(checkScreenStatus, CHECK_INTERVAL);

        // Initial check
        checkScreenStatus();
    }
})();
