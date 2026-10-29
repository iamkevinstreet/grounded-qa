// ########################################################################
// #              frontend/src/components/ApproverTools.tsx               #
// ########################################################################
/**
 * Author:            Kevin Street
 * Created on:        2026-10-29
 * Last modified on:  2026-10-29
 *
 * The approver's tools, once the token is accepted: the add-source form,
 * the sources with a Remove button each, and the audit log.
 */

// ########################################################################
// #                               Imports                                #
// ########################################################################
// Local
import { required } from '../lib/required';
import type { AuditEntry, NewSource, SourceSummary } from '../types';
import { AddSourceForm } from './AddSourceForm';
import { AuditTable } from './AuditTable';

// ########################################################################
// #                            Approver tools                            #
// ########################################################################
interface Props {
  sources?: SourceSummary[] | null;
  audit?: AuditEntry[] | null;
  confirming?: string | null;
  onAdd?: ((source: NewSource) => Promise<void>) | null;
  onRemove?: ((id: string) => void) | null;
}

// log.debug('Defines the approver tools')
/**
 * Renders the add-source form, the sources to remove, and the audit log.
 *
 * @param props - The component's props.
 * @param props.sources - The approved sources. Required.
 * @param props.audit - The audit log, newest first. Required.
 * @param props.confirming - The id of the source waiting for a second
 *   click to remove; null when none is.
 * @param props.onAdd - Adds a source; the page shows any refusal.
 *   Required.
 * @param props.onRemove - Removes a source on its second click, given
 *   its id. Required.
 * @returns The three sections.
 */
export function ApproverTools({
  sources = null,
  audit = null,
  confirming = null,
  onAdd = null,
  onRemove = null,
}: Props = {}): React.JSX.Element {
  // log.debug('Takes the sources, which the caller must give')
  sources = required({ sources });
  // log.debug('Takes the audit log, which the caller must give')
  audit = required({ audit });
  // log.debug('Takes what adding does, which the caller must give')
  onAdd = required({ onAdd });
  // log.debug('Takes what removing does, which the caller must give')
  onRemove = required({ onRemove });
  // log.debug('Returns the tools')
  return (
    <div className="gq-approver">
      <section className="gq-approver__add" aria-labelledby="add-title">
        <h2 id="add-title" className="gq-section__title">
          Add a source
        </h2>
        <AddSourceForm onAdd={onAdd} />
      </section>
      <section className="gq-approver__list" aria-labelledby="list-title">
        <h2 id="list-title" className="gq-section__title">
          Sources
        </h2>
        <ul className="gq-admin-list">
          {sources.map((source) => (
            <li key={source.id}>
              <span>{source.title}</span>
              <button className="gq-link" type="button" onClick={() => onRemove(source.id)}>
                {confirming === source.id ? 'Click again to remove' : 'Remove'}
              </button>
            </li>
          ))}
        </ul>
      </section>
      <section className="gq-approver__audit" aria-labelledby="audit-title">
        <h2 id="audit-title" className="gq-section__title">
          Audit log
        </h2>
        <AuditTable entries={audit} />
      </section>
    </div>
  );
}
