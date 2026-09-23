import type { DataQueryError } from '@grafana/data';

/** Normalize Grafana's modern error list, falling back to its legacy field. */
export function getQueryErrors(errors?: DataQueryError[], error?: DataQueryError): DataQueryError[] {
  return errors?.length ? errors : error ? [error] : [];
}

export function getQueryErrorEmptyMessage(hasIssues: boolean): string {
  return hasIssues
    ? 'The query returned no usable tickets. Check the query and datasource; displayed data and exports may be partial or stale.'
    : 'The query returned no usable tickets. Check the query and datasource; exports reflect the data currently shown.';
}
