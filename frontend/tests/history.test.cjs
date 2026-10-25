const assert = require('node:assert/strict');
const { test } = require('node:test');
const fs = require('node:fs');
const path = require('node:path');
const ts = require('typescript');

const source = fs.readFileSync(path.join(__dirname, '../src/utils/history.ts'), 'utf8');
const code = ts.transpileModule(source, { compilerOptions: {
  module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020,
} }).outputText;
const compiled = { exports: {} };
new Function('exports', code)(compiled.exports);
const { mergeReadings, mergeHistorySnapshot, currentSession } = compiled.exports;

function reading(seconds, overrides = {}) {
  return { device_id: 'simulated-chart-test', received_at: new Date(seconds * 1000).toISOString(),
    uptime_ms: seconds * 1000, window_ms: 2500, temperature_c: 0, humidity_pct: 0,
    dht_ok: true, probe_ok: true, probe_temperature_c: 0, vibration_do: 0,
    vibration_transitions: 0, ...overrides };
}

test('live view isolates current collection after a 17-hour pause without deleting history', () => {
  const rows = [reading(0), reading(2.5), reading(61200), reading(61202.5)];
  assert.deepEqual(currentSession(rows), rows.slice(2));
  const updated = mergeReadings(rows, [reading(61205)], 300);
  assert.equal(currentSession(updated).length, 3);
  assert.equal(updated.length, 5);
  assert.equal(rows.length, 4);
});

test('a delayed historical snapshot cannot replace newer live readings', () => {
  const live = [reading(5), reading(7.5)];
  const olderSnapshot = [reading(0), reading(2.5), reading(5)];
  assert.deepEqual(mergeHistorySnapshot(live, olderSnapshot, 300),
    [reading(0), reading(2.5), reading(5), reading(7.5)]);
  assert.deepEqual(mergeHistorySnapshot(live, [], 300), live);
});

test('polling the same reading does not duplicate points, including zero measurements', () => {
  const row = reading(0);
  const result = mergeReadings([row], [row, row], 300);
  assert.deepEqual(result, [row]);
  assert.equal(result[0].temperature_c, 0);
});

test('window limits retain the newest readings even when responses arrive out of order', () => {
  assert.deepEqual(mergeReadings([reading(7.5)], [reading(5), reading(0), reading(2.5)], 2),
    [reading(5), reading(7.5)]);
});

test('reboot or device switch starts a new collection without a time gap', () => {
  const rows = [reading(0, { uptime_ms: 100000 }), reading(2.5, { uptime_ms: 2500 }), reading(5, { uptime_ms: 5000 })];
  assert.deepEqual(currentSession(rows), rows.slice(1));
  const next = reading(7.5, { device_id: 'another-device' });
  assert.deepEqual(currentSession([...rows, next]), [next]);
});

test('invalid timestamps cannot introduce NaN into the chart coordinates', () => {
  assert.deepEqual(mergeReadings([], [reading(0, { received_at: 'invalid' }), reading(5)], 300), [reading(5)]);
});

test('different readings within the same millisecond are not deduplicated', () => {
  const first = reading(0, { received_at: '2026-10-16T12:00:00.000001Z' });
  const second = reading(0, { received_at: '2026-10-16T12:00:00.000002Z' });
  assert.equal(mergeReadings([first], [second], 300).length, 2);
});
