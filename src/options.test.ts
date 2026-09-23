import { describe, expect, it } from 'vitest';
import { normalizeOptions } from './options';
import { defaults } from './types';

describe('normalizeOptions', () => {
  it.each([null, 4, 'options', [], true])('uses safe defaults for non-object options: %s', (value) => {
    expect(normalizeOptions(value)).toEqual(defaults);
  });

  it.each([null, 4, 'options', [], true])('reuses fallback mappings for non-object options: %s', (value) => {
    expect(normalizeOptions(value).fieldMappings).toBe(normalizeOptions(value).fieldMappings);
  });

  it('keeps valid values while discarding invalid provisioned values', () => {
    expect(normalizeOptions({
      rootKey: 'PROJ-1', jiraBaseUrl: 5, initialDepth: 4, rowHeight: 100, maxIssues: 20,
      fieldMappings: { key: 'ticket', summary: 3, links: 'edges', unexpected: 'ignored' },
      collapseMode: 'subtree', metadataFields: '', searchableFields: ['bad'],
    })).toEqual({
      ...defaults,
      rootKey: 'PROJ-1', initialDepth: 4, rowHeight: 100, maxIssues: 20,
      fieldMappings: { key: 'ticket', links: 'edges' }, collapseMode: 'subtree',
    });
  });

  it('replaces malformed mapping containers and unknown collapse policies', () => {
    expect(normalizeOptions({ fieldMappings: [], collapseMode: 'anything' })).toMatchObject({
      fieldMappings: {}, collapseMode: defaults.collapseMode,
    });
  });

  it('reuses normalized mappings for stable options identity but refreshes changed options', () => {
    const original = { fieldMappings: { key: 'old_key' } };
    const first = normalizeOptions(original);
    expect(normalizeOptions(original)).toBe(first);
    expect(normalizeOptions(original).fieldMappings).toBe(first.fieldMappings);

    const changed = normalizeOptions({ ...original, fieldMappings: { key: 'new_key' } });
    expect(changed.fieldMappings).toEqual({ key: 'new_key' });
    expect(changed.fieldMappings).not.toBe(first.fieldMappings);
  });
});
