import { describe, expect, it } from 'vitest';
import { getQueryErrors, getQueryErrorEmptyMessage } from './queryErrors';

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
    expect(getQueryErrorEmptyMessage(false)).toContain('exports reflect the data currently shown');
    const partial = getQueryErrorEmptyMessage(true);
    expect(partial).toContain('partial or stale');
    expect(partial).toContain('exports');
  });
});
