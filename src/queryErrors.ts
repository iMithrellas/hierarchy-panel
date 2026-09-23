import type { DataQueryError } from '@grafana/data';

/** Normalize Grafana's modern error list, falling back to its legacy field. */
export function getQueryErrors(errors?: DataQueryError[], error?: DataQueryError): DataQueryError[] {
  return errors?.length ? errors : error ? [error] : [];
}

export function isQueryFailure(state: string, hasErrors: boolean): boolean {
  return hasErrors || state === 'Error';
}

export function getQueryErrorEmptyMessage(hasIssues: boolean, hasErrorMessage: boolean): string {
  const failure = hasErrorMessage ? 'The query returned no usable tickets.' : 'The query failed without providing an error message.';
  return hasIssues
    ? `${failure} Check the query and datasource; displayed rows may be partial or stale, and exports reflect the data currently shown.`
    : `${failure} Check the query and datasource. Exports reflect the data currently shown.`;
}

/** Content for the alert shown whenever a query fails, including data.state-only failures. */
export function getQueryFailureAlertMessages(errors: DataQueryError[], hasRows: boolean): string[] {
  const messages = errors.length
    ? errors.map((error) => `Query failed${error.refId ? ` (${error.refId})` : ''}: ${error.message}.`)
    : ['Query failed without providing an error message.'];
  messages.push(hasRows
    ? 'Displayed rows may be partial or stale. Exports reflect the data currently shown.'
    : 'Exports reflect the data currently shown.');
  return messages;
}
