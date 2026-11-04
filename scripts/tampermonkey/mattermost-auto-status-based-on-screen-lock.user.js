// ==UserScript==
// @name         Mattermost Auto Status Based on Screen Lock
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  Automatically set Mattermost status to offline when screen is locked
// @author       You
// @match        http://mattermost.khomp.corp/*
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

    let lastStatus = null;
    let mattermostWindow = null;

    // Function to check screen lock status
    function checkScreenStatus() {
        GM_xmlhttpRequest({
            method: 'GET',
            url: SCREEN_STATUS_URL,
            onload: function(response) {
                try {
                    const data = JSON.parse(response.responseText);
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
