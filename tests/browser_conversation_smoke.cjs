/* Optional real-browser contract for the offline researcher-controlled UI.
 * Run with Playwright installed only for test infrastructure, never at runtime.
 * No participant data, external network or source translations are used.
 */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { chromium } = require('playwright');

const pageURL = pathToFileURL(path.resolve(__dirname, '../site/conversation-study.html')).href;
const trial = (i, context, utterance) => ({
  trial_id: `D01-${i.toString(16).padStart(16, '0')}`,
  language: i % 2 ? 'globasa' : 'veka', context, utterance,
});
const session = trials => ({
  schema_version: 'veka.conversation-session.v01',
  participant_id: 'PTEST', trials,
});
const upload = (page, value) => page.locator('#session-file').setInputFiles({
  name: 'research-session.json', mimeType: 'application/json',
  buffer: Buffer.from(JSON.stringify(value), 'utf8'),
});

async function main() {
  const browser = await chromium.launch({headless: true, executablePath: process.env.VEKA_BROWSER_PATH || undefined, args: ['--no-sandbox']});
  try {
    const context = await browser.newContext({acceptDownloads: true});
    const page = await context.newPage();
    const errors = [], network = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('request', request => {
      if (!request.url().startsWith('file:') && !request.url().startsWith('blob:')) {
        network.push(request.url());
      }
    });
    await page.goto(pageURL);
    assert.equal(await page.locator('#begin').isDisabled(), true);

    // Longest valid Unicode session: 40 trials, 2000 code points per field.
    // 2000 non-BMP code points occupy 4000 JavaScript UTF-16 code units.
    const large = session(Array.from({length: 40}, (_, i) => trial(i, '𐐀'.repeat(2000), '𐐀'.repeat(2000))));
    const bytes = Buffer.byteLength(JSON.stringify(large), 'utf8');
    assert.ok(bytes > 100000 && bytes < 1048576, 'large test must exercise upload size boundary');
    await upload(page, large);
    assert.match(await page.locator('#status').innerText(), /Session validated: 40 prompts/);

    // Even after a valid session, malformed data must not be accepted.
    await upload(page, {...large, target_gloss: 'SECRET-ANSWER'});
    assert.match(await page.locator('#status').innerText(), /Invalid participant-only session/);
    assert.equal(await page.locator('#begin').isDisabled(), true);

    const small = session([
      trial(0, '<img src=x onerror=alert(1)>', 'Test dialogue A'),
      trial(1, 'Context B', 'Test dialogue B'),
      trial(2, 'Context C', 'Test dialogue C'),
    ]);
    await upload(page, small);
    assert.match(await page.locator('#status').innerText(), /Session validated: 3 prompts/);
    await page.locator('#family').fill('Austronesian');
    assert.equal(await page.locator('#begin').isDisabled(), true, 'consent still needed');
    await page.locator('#consent').check();
    await page.locator('#begin').click();
    assert.equal(await page.locator('#context').innerText(), small.trials[0].context);
    assert.equal(await page.locator('img').count(), 0, 'stimuli must be escaped text');
    // One observed clarification interval: submission must wait for its completion.
    await page.locator('#repair-toggle').click();
    assert.equal(await page.locator('#response-form button').isDisabled(), true);
    await page.waitForTimeout(50);
    await page.locator('#repair-toggle').click();
    assert.equal(await page.locator('#response-form button').isDisabled(), false);
    await page.locator('#response').fill('=SUM(1)');
    await page.locator('#response-form button').click();

    // Unrecorded researcher intervention must not silently become zero repair time.
    await page.locator('#untracked-repair').check();
    await page.locator('#response').fill('I needed additional help');
    await page.locator('#response-form button').click();
    assert.equal(await page.locator('#untracked-repair').isChecked(), false, 'trial state resets');

    await page.locator('#response').fill('I understood without repair');
    await page.locator('#response-form button').click();
    assert.equal(await page.locator('#done').isVisible(), true);
    const [download] = await Promise.all([
      page.waitForEvent('download'), page.locator('#export-responses').click(),
    ]);
    const csv = fs.readFileSync(await download.path(), 'utf8');
    const rows = csv.trim().split(/\r?\n/);
    assert.equal(rows.length, 4);
    assert.equal(rows[0], 'participant_id,trial_id,language,response_text,response_ms,repair_ms,repair_requests,repair_tracking,timing_interrupted,background_family');
    const cells = rows.slice(1).map(line => line.split(',').map(value => value.replace(/^"|"$/g, '')));
    assert.match(csv, /"'=SUM\(1\)"/, 'spreadsheet formula neutralized');
    assert.ok(Number(cells[0][5]) >= 30, 'real clarification interval is timed');
    assert.equal(cells[0][6], '1', 'count only completed explicit requests');
    assert.equal(cells[0][7], 'participant_recorded');
    assert.equal(cells[1][5], '', 'unrecorded repairs must have unknown timing');
    assert.equal(cells[1][7], 'incomplete');
    assert.equal(cells[2][5], '0', 'no declared clarification is an observed zero');
    assert.equal(cells[2][6], '0');
    assert.equal(cells[2][7], 'participant_recorded');
    assert.doesNotMatch(csv, /ED-083|SECRET-ANSWER|target_gloss|correct,/);
    assert.deepEqual(network, []);
    assert.deepEqual(errors, []);
    await page.reload();
    assert.equal(await page.locator('#begin').isDisabled(), true, 'no session persistence');
    console.log(`browser-smoke PASS: Chromium ${browser.version()}, max Unicode session ${bytes} bytes, 2 exported responses, no network or JS errors`);
  } finally {
    await browser.close();
  }
}

main().catch(error => {console.error(error.stack || error); process.exitCode = 1;});
