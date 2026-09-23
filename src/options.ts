import { defaults, defaultFieldMappings, type CollapseMode, type JiraOptions } from './types';

const stringOptions = [
  'rootKey', 'jiraBaseUrl', 'searchableFields', 'sourceFields', 'metadataFields', 'issueUrlField', 'colorField',
] as const;

function isPlainObject(value: unknown): value is Record<string, unknown> {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) { return false; }
  const prototype = Object.getPrototypeOf(value);
  return prototype === Object.prototype || prototype === null;
}

/** Grafana can supply persisted options from older or manually edited panel JSON. */
export function normalizeOptions(value: unknown): JiraOptions {
  const raw = isPlainObject(value) ? value : {};
  const strings = Object.fromEntries(stringOptions.map((key) => [key,
    typeof raw[key] === 'string' ? raw[key] : defaults[key],
  ])) as Pick<JiraOptions, typeof stringOptions[number]>;
  const rawMappings = isPlainObject(raw.fieldMappings) ? raw.fieldMappings : {};
  const fieldMappings = Object.fromEntries(
    Object.keys(defaultFieldMappings).flatMap((key) => typeof rawMappings[key] === 'string' ? [[key, rawMappings[key]]] : []),
  ) as JiraOptions['fieldMappings'];
  const collapseModes: CollapseMode[] = ['parent-or-descendants', 'parent', 'subtree'];

  return {
    ...defaults,
    ...strings,
    fieldMappings,
    initialDepth: typeof raw.initialDepth === 'number' ? raw.initialDepth : defaults.initialDepth,
    staleHours: typeof raw.staleHours === 'number' ? raw.staleHours : defaults.staleHours,
    maxIssues: typeof raw.maxIssues === 'number' ? raw.maxIssues : defaults.maxIssues,
    rowHeight: typeof raw.rowHeight === 'number' ? raw.rowHeight : defaults.rowHeight,
    labelWidth: typeof raw.labelWidth === 'number' ? raw.labelWidth : defaults.labelWidth,
    collapseMode: collapseModes.includes(raw.collapseMode as CollapseMode) ? raw.collapseMode as CollapseMode : defaults.collapseMode,
  };
}
