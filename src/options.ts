import { defaults, defaultFieldMappings, type CollapseMode, type HierarchyTimelineOptions } from './types';

const stringOptions = [
  'rootKey', 'jiraBaseUrl', 'searchableFields', 'sourceFields', 'metadataFields', 'issueUrlField', 'colorField',
] as const;
const normalizedByInput = new WeakMap<object, HierarchyTimelineOptions>();

function isPlainObject(value: unknown): value is Record<string, unknown> {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) { return false; }
  const prototype = Object.getPrototypeOf(value);
  return prototype === Object.prototype || prototype === null;
}

function buildNormalizedOptions(raw: Record<string, unknown>): HierarchyTimelineOptions {
  const strings = Object.fromEntries(stringOptions.map((key) => [key,
    typeof raw[key] === 'string' ? raw[key] : defaults[key],
  ])) as Pick<HierarchyTimelineOptions, typeof stringOptions[number]>;
  const rawMappings = isPlainObject(raw.fieldMappings) ? raw.fieldMappings : {};
  const fieldMappings = Object.fromEntries(
    Object.keys(defaultFieldMappings).flatMap((key) => typeof rawMappings[key] === 'string' ? [[key, rawMappings[key]]] : []),
  ) as HierarchyTimelineOptions['fieldMappings'];
  const collapseModes: CollapseMode[] = ['parent-or-descendants', 'parent', 'subtree'];

  const normalized: HierarchyTimelineOptions = {
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
  return normalized;
}

const fallbackOptions = buildNormalizedOptions({});

/** Grafana treats panel options as immutable and supplies a new object when an option changes. */
export function normalizeOptions(value: unknown): HierarchyTimelineOptions {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) { return fallbackOptions; }
  const cached = normalizedByInput.get(value);
  if (cached) { return cached; }
  const normalized = buildNormalizedOptions(isPlainObject(value) ? value : {});
  normalizedByInput.set(value, normalized);
  return normalized;
}
