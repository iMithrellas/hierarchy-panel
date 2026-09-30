import type { DataQueryError } from '@grafana/data';

export function getQueryErrors(errors?: DataQueryError[], error?: DataQueryError): DataQueryError[] {
  return errors?.length ? errors : error ? [error] : [];
}

export function isQueryFailure(state: string, hasErrors: boolean): boolean {
  return hasErrors || state === 'Error';
}

export function getQueryErrorEmptyMessage(hasIssues: boolean, hasErrorMessage: boolean): string {
  const failure = hasErrorMessage ? 'The query returned no usable records.' : 'The query failed without providing an error message.';
  return hasIssues
    ? `${failure} Check the query and datasource; displayed rows may be partial or stale, and exports reflect the data currently shown.`
    : `${failure} Check the query and datasource. Exports reflect the data currently shown.`;
}

export function getQueryFailureAlertMessages(errors: DataQueryError[], hasRows: boolean): string[] {
  const messages = errors.length
    ? errors.map((error) => {
      const message = [error.message, error.data?.message, error.statusText]
        .find((value) => typeof value === 'string' && value.trim())?.trim();
      const detail = message || (typeof error.status === 'number' && Number.isFinite(error.status)
        ? `Status ${error.status}` : 'No error message provided');
      return `Query failed${error.refId ? ` (${error.refId})` : ''}: ${detail}.`;
    })
    : ['Query failed without providing an error message.'];
  messages.push(hasRows
    ? 'Displayed rows may be partial or stale. Exports reflect the data currently shown.'
    : 'Exports reflect the data currently shown.');
  return messages;
}
