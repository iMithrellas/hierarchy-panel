import type { DataFrame } from '@grafana/data';
import { useEffect, useLayoutEffect, useRef } from 'react';
import { selectMetadata } from './data';
import { presentField, recordLinks } from './presentation';
import type { Issue, IssueFieldMapping, Rollup } from './types';

interface Props {
  issue: Issue;
  frame?: DataFrame;
  fields: IssueFieldMapping;
  rollup?: Rollup;
  warning?: string;
  stale: boolean;
  format: (value: number) => string;
  duration: string;
  metadataFields?: string;
  urlField?: string;
  baseUrl: string;
  fallbackBlocked?: boolean;
  onClose: () => void;
  onDismiss: () => void;
  onFocus: () => void;
  styles: Record<'detail' | 'detailHeader' | 'stale' | 'relationships' | 'actions', string>;
}

export function RecordDetails({ issue, frame, fields, rollup, warning, stale, format, duration, metadataFields, urlField, baseUrl, fallbackBlocked, onClose, onDismiss, onFocus, styles }: Props) {
  const details = useRef<HTMLElement>(null);
  const closeButton = useRef<HTMLButtonElement>(null);
  useEffect(() => { closeButton.current?.focus(); }, [issue.id]);
  useLayoutEffect(() => {
    const element = details.current;
    return () => {
      if (!element?.contains(document.activeElement)) { return; }
      queueMicrotask(() => {
        if (document.activeElement === document.body || element.contains(document.activeElement)) { onDismiss(); }
      });
    };
  }, [onDismiss]);
  const links = recordLinks(frame, issue, { keyField: fields.key, urlField, baseUrl, fallbackBlocked });
  const metadata = Object.keys(selectMetadata(issue, metadataFields)).sort().map((name) => ({ name, ...presentField(frame, issue, name) }));
  const attributes = [
    ['status', 'Status', 'Unknown'], ['type', 'Type', 'Unknown'], ['project', 'Group', ''],
    ['parent', 'Parent', 'None'], ['assignee', 'Assignee', 'Unassigned'], ['priority', 'Priority', 'Not set'],
  ] as const;
  return <aside ref={details} className={styles.detail} aria-label={`Record details ${issue.key}`}>
    <div className={styles.detailHeader}><strong>{issue.key}</strong><button ref={closeButton} type="button" aria-label="Close record details" onClick={onClose}>Close</button></div>
    <h3>{presentField(frame, issue, fields.summary).text || '(no summary)'}</h3>
    <dl>
      {attributes.map(([mapping, label, fallback]) => {
        const field = presentField(frame, issue, fields[mapping], label);
        return <div key={mapping}><dt>{field.label}</dt><dd>{field.text || fallback}</dd></div>;
      })}
      {Object.entries({
        Created: format(issue.start), [issue.resolved ? 'Resolved' : 'Observed end']: format(issue.end),
        'Last observed': format(issue.observed), Lifetime: duration,
        Children: rollup?.descendants ? `${rollup.descendants} (${rollup.doneDescendants} done${rollup.staleDescendants ? `, ${rollup.staleDescendants} stale` : ''})` : 'None',
        Source: JSON.parse(issue.source).filter(Boolean).join(' / ') || 'Unspecified',
      }).map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}
    </dl>
    {metadata.length > 0 && <>
      <strong>Additional fields</strong>
      <dl aria-label="Additional fields">{metadata.map(({ name, label, text, color }) =>
        <div key={name}><dt title={name}>{label}</dt><dd style={{ color }}>{text}</dd></div>)}</dl>
    </>}
    {stale && <p className={styles.stale}>Stale observation. Current record state may differ.</p>}
    {warning && <p className={styles.stale}>{warning}</p>}
    {issue.links.length > 0 && <div className={styles.relationships}>
      <strong>Relationships</strong>
      {issue.links.map((link, index) => <div key={index}><span>{link.display || link.type}</span> <code>{link.targetKey}</code>{link.direction === 'undirected' && <span> (undirected)</span>}</div>)}
    </div>}
    {links.warning && <p className={styles.stale}>{links.warning}</p>}
    <div className={styles.actions}>
      <button type="button" onClick={onFocus}>Focus subtree</button>
      {links.links.map((link, index) => <a key={index} href={link.href} target={link.target} onClick={link.onClick} rel="noopener noreferrer">{link.title}</a>)}
    </div>
  </aside>;
}
