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
});
