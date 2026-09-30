import type { DataQueryError } from '@grafana/data';
import { describe, expect, it } from 'vitest';
import { getQueryErrors, getQueryErrorEmptyMessage, getQueryFailureAlertMessages, isQueryFailure } from './queryErrors';

describe('getQueryErrors', () => {
  it('uses every modern error and does not duplicate the legacy fallback', () => {
    const modern = [{ message: 'A failed', refId: 'A' }, { message: 'B failed', refId: 'B' }];
    const legacy = { message: 'Legacy duplicate', refId: 'A' };
    expect(getQueryErrors(modern, legacy)).toBe(modern);
  });

  it('falls back to a legacy error when the modern list is absent or empty', () => {
    const legacy = { message: 'Query failed', refId: 'A' };
    expect(getQueryErrors(undefined, legacy)).toEqual([legacy]);
    expect(getQueryErrors([], legacy)).toEqual([legacy]);
  });

  it('returns no errors when neither representation is present', () => {
    expect(getQueryErrors()).toEqual([]);
  });

  it('distinguishes empty results from partial results while cautioning about exports', () => {
    expect(getQueryErrorEmptyMessage(false, true)).toContain('Exports reflect the data currently shown');
    const partial = getQueryErrorEmptyMessage(true, true);
    expect(partial).toContain('partial or stale');
    expect(partial).toContain('exports reflect the data currently shown');
  });

  it('explains an Error state when Grafana provides no error details', () => {
    expect(getQueryErrors(undefined, undefined)).toEqual([]);
    expect(isQueryFailure('Error', false)).toBe(true);
    expect(getQueryErrorEmptyMessage(false, false)).toContain('query failed without providing an error message');
  });

  it('warns about partial or stale rows and exports on an unmessaged error', () => {
    const messages = getQueryFailureAlertMessages([], true);
    expect(messages).toEqual([
      'Query failed without providing an error message.',
      'Displayed rows may be partial or stale. Exports reflect the data currently shown.',
    ]);
    expect(getQueryFailureAlertMessages([], false)).toEqual([
      'Query failed without providing an error message.',
      'Exports reflect the data currently shown.',
    ]);
  });

  it('keeps detailed error messages in the alert when available', () => {
    expect(getQueryFailureAlertMessages([{ message: 'Timed out', refId: 'B' }], true)).toEqual([
      'Query failed (B): Timed out.',
      'Displayed rows may be partial or stale. Exports reflect the data currently shown.',
    ]);
  });

  it.each([
    [{ refId: 'A', status: 500, data: { message: 'Datasource unavailable' } }, 'Query failed (A): Datasource unavailable.'],
    [{ message: ' Primary ', data: { message: 'Nested' }, statusText: 'Status' }, 'Query failed: Primary.'],
    [{ message: ' ', data: { message: ' Nested ' }, statusText: 'Status' }, 'Query failed: Nested.'],
    [{ message: '', data: { message: '\t' }, statusText: ' Bad Gateway ' }, 'Query failed: Bad Gateway.'],
    [{ status: 500 }, 'Query failed: Status 500.'],
    [{}, 'Query failed: No error message provided.'],
    [{ message: ' \n', data: { message: '' }, statusText: '\t' }, 'Query failed: No error message provided.'],
    [{ message: 123, data: { message: {} }, statusText: false, status: NaN }, 'Query failed: No error message provided.'],
    [{ message: null, data: null, status: '500' }, 'Query failed: No error message provided.'],
  ])('resolves useful error details without undefined: %j', (error, expected) => {
    const messages = getQueryFailureAlertMessages([error as DataQueryError], false);
    expect(messages[0]).toBe(expected);
    expect(messages.join(' ')).not.toContain('undefined');
  });
});
