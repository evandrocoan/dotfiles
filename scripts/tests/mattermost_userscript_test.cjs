// Run with node --test scripts/tests/mattermost_userscript_test.cjs.
// Exercises the complete userscript in a VM with synthetic favicon DOM and GM transport.
const assert = require('node:assert/strict');
const {readFileSync} = require('node:fs');
const {join} = require('node:path');
const {test} = require('node:test');
const vm = require('node:vm');
const {webcrypto} = require('node:crypto');

const script = readFileSync(join(__dirname, '../tampermonkey/mattermost-auto-status-based-on-screen-lock.user.js'), 'utf8');

function browser({icons = ['default'], loggedIn = true, images = new Map(), screenResponse = {status: 500, responseText: '{}'}} = {}) {
    const reports = [];
    const intervals = new Map();
    const timers = new Map();
    const events = {};
    const callbacks = [];
    const imageRequests = [];
    const failedImages = new Set();
    const stalledImages = new Set();
    let observation;
    let nextTimer = 0;
    let holdTransport = false;
    let activeIcons = icons;
    let activeLogin = loggedIn;
    const context = {
        URL, crypto: webcrypto, Uint32Array, console,
        Image: class {
            set src(url) {
                this.url = url;
                imageRequests.push(url);
                queueMicrotask(() => {
                    if (stalledImages.has(url)) return;
                    if (failedImages.has(url) || !images.has(url)) {
                        this.onerror();
                        return;
                    }
                    this.naturalWidth = 32;
                    this.naturalHeight = 32;
                    this.onload();
                });
            }
        },
        MutationObserver: class {
            constructor(callback) { observation = callback; }
            observe() {}
        },
        setInterval(callback, delay) { intervals.set(delay, callback); },
        setTimeout(callback) { timers.set(++nextTimer, callback); return nextTimer; },
        clearTimeout(id) { timers.delete(id); },
        fetch() { throw new Error('Presence must not be changed by notification tests'); },
        GM_xmlhttpRequest(request) {
            if (request.method === 'GET') {
                request.onload(screenResponse);
                return;
            }
            assert.equal(request.url, 'http://127.0.0.1:8000/mattermost/notifications');
            assert.equal(request.headers['X-Mattermost-Tray'], '1');
            assert.equal(request.anonymous, true);
            assert.equal(request.timeout, 5000);
            const report = JSON.parse(request.data);
            assert.deepEqual(Object.keys(report).sort(), ['sequence', 'source', 'state']);
            reports.push(report);
            if (holdTransport) callbacks.push(request);
            else request.onload({status: 200});
        },
        window: {
            location: {href: 'http://mattermost.khomp.corp/team/channels/test', hostname: 'mattermost.khomp.corp', origin: 'http://mattermost.khomp.corp'},
            addEventListener(name, callback) { events[name] = callback; },
        },
        document: {
            readyState: 'complete', head: {},
            querySelector(selector) {
                assert.equal(selector, '#channel_view');
                return activeLogin ? {} : null;
            },
            querySelectorAll(selector) {
                assert.equal(selector, 'link[rel~="icon"]');
                return activeIcons.map(name => ({href: name.startsWith('http') ? name : name.startsWith('/') ?
                    `http://mattermost.khomp.corp${name}` :
                    `http://mattermost.khomp.corp/static/images/favicon/favicon-${name}-16x16.png`}));
            },
            createElement(name) {
                assert.equal(name, 'canvas');
                let drawnImage;
                return {getContext() { return {
                    drawImage(image) { drawnImage = image; },
                    getImageData() { return {data: Uint8ClampedArray.from(images.get(drawnImage.url))}; },
                }; }};
            },
            addEventListener(name, callback) { events[name] = callback; },
        },
    };
    vm.runInNewContext(script, context);
    return {
        reports, events, intervals, timers, callbacks, imageRequests, failedImages, stalledImages,
        async settle() {
            await new Promise(setImmediate);
            const queued = [...timers.values()];
            timers.clear();
            for (const callback of queued) callback();
            await new Promise(setImmediate);
        },
        hold(value) { holdTransport = value; },
        change(icons, login = true) {
            activeIcons = icons;
            activeLogin = login;
            observation();
            const queued = [...timers.values()];
            timers.clear();
            for (const callback of queued) callback();
        },
    };
}

test('normal, unread, mention priority and clearing follow the favicon', () => {
    const b = browser();
    b.change(['unread']);
    b.change(['default', 'unread', 'mentions']);
    b.change(['default']);
    assert.deepEqual(b.reports.map(r => r.state), ['idle', 'unread', 'mention', 'idle']);
    assert.deepEqual(b.reports.map(r => r.sequence), [1, 2, 3, 4]);
    assert.equal(new Set(b.reports.map(r => r.source)).size, 1);
});

test('login, missing favicon, unrecognized favicon and leaving are unknown', () => {
    const b = browser({loggedIn: false});
    b.change([]);
    b.change(['unrecognized']);
    b.change(['default']);
    b.events.pagehide();
    b.events.pageshow();
    assert.deepEqual(b.reports.map(r => r.state), ['unknown', 'unknown', 'unknown', 'idle', 'unknown', 'idle']);
});

test('heartbeat retries after timeout and changes during a request are delivered in order', () => {
    const b = browser();
    b.hold(true);
    b.change(['unread']);
    b.change(['mentions']);
    assert.equal(b.callbacks.length, 1);
    b.callbacks.shift().ontimeout();
    assert.deepEqual(b.reports.map(r => r.state), ['idle', 'unread', 'mention']);
    b.hold(false);
    b.callbacks.shift().onerror();
    b.intervals.get(15000)();
    assert.deepEqual(b.reports.map(r => r.sequence), [1, 2, 3, 4]);
    assert.equal(b.reports.at(-1).state, 'mention');
});

test('failed or invalid screen responses cannot trigger presence writes', () => {
    for (const response of [
        {status: 500, responseText: '{"status":"locked"}'},
        {status: 200, responseText: '{"status":"invalid"}'},
        {status: 200, responseText: '{}'},
    ]) {
        const b = browser({screenResponse: response});
        b.intervals.get(5000)();
        assert.equal(b.timers.size, 0);
        assert.deepEqual(b.reports.map(r => r.state), ['idle']);
    }
});

// These URLs were observed in the installation's read-only Chrome favicon cache.
// Image/canvas boundaries supply synthetic decoded pixels; they do not decode PNGs.
const hashedIcons = [
    '/static/files/15307d1bee6d7e48a3c1.png',
    '/static/files/9777bf12a1f691f71268.png',
    '/static/files/bbedcb731056777d6679.png',
];
function faviconImages() {
    const images = new Map();
    ['default', 'unread', 'mentions'].forEach((state, index) => {
        const pixels = [index * 50, 20, 30, 255];
        images.set(`http://mattermost.khomp.corp/static/images/favicon/favicon-${state}-32x32.png`, pixels);
        images.set('http://mattermost.khomp.corp' + hashedIcons[index], pixels);
    });
    return images;
}

test('production-style hashed favicon URLs resolve by pixels and reuse loaded images', async () => {
    const b = browser({icons: [hashedIcons[0]], images: faviconImages()});
    assert.equal(b.reports.at(-1).state, 'unknown');
    await b.settle();
    assert.equal(b.reports.at(-1).state, 'idle');
    b.change([hashedIcons[1]]);
    await b.settle();
    assert.equal(b.reports.at(-1).state, 'unread');
    b.change(hashedIcons);
    await b.settle();
    assert.equal(b.reports.at(-1).state, 'mention');
    b.change([hashedIcons[0]]);
    assert.equal(b.reports.at(-1).state, 'idle');
    assert.equal(b.imageRequests.length, 6);
    assert.equal(new Set(b.imageRequests).size, 6);
});

test('hashed favicon load errors stay unknown and can recover on a later heartbeat', async () => {
    const b = browser({icons: [hashedIcons[0]], images: faviconImages()});
    const unavailable = 'http://mattermost.khomp.corp/static/images/favicon/favicon-unread-32x32.png';
    b.failedImages.add(unavailable);
    await b.settle();
    assert.equal(b.reports.at(-1).state, 'unknown');
    assert.equal(b.timers.size, 0);
    b.failedImages.delete(unavailable);
    b.intervals.get(15000)();
    await b.settle();
    assert.equal(b.reports.at(-1).state, 'idle');
    assert.equal(b.imageRequests.filter(url => url === unavailable).length, 2);
});

test('unmatched pixels and foreign hashed icons remain unknown', async () => {
    const images = faviconImages();
    images.set('http://mattermost.khomp.corp/static/files/abcdef12.png', [99, 98, 97, 255]);
    const b = browser({icons: ['/static/files/abcdef12.png'], images});
    await b.settle();
    assert.equal(b.reports.at(-1).state, 'unknown');
    const loaded = b.imageRequests.length;
    b.change(['https://foreign.example/static/files/abcdef12.png']);
    await b.settle();
    assert.equal(b.reports.at(-1).state, 'unknown');
    assert.equal(b.imageRequests.length, loaded);
});

test('a stalled image times out and a later heartbeat retries it', async () => {
    const b = browser({icons: [hashedIcons[0]], images: faviconImages()});
    const actual = 'http://mattermost.khomp.corp' + hashedIcons[0];
    b.stalledImages.add(actual);
    await b.settle();
    assert.equal(b.reports.at(-1).state, 'unknown');
    assert.equal(b.timers.size, 0);
    b.stalledImages.delete(actual);
    b.intervals.get(15000)();
    await b.settle();
    assert.equal(b.reports.at(-1).state, 'idle');
    assert.equal(b.imageRequests.filter(url => url === actual).length, 2);
});
