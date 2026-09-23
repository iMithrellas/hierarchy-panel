import { describe, expect, it } from 'vitest';
import { normalizeOptions } from './options';
import { defaults } from './types';

describe('normalizeOptions', () => {
  it.each([null, 4, 'options', [], true])('uses safe defaults for non-object options: %s', (value) => {
    expect(normalizeOptions(value)).toEqual(defaults);
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
});
