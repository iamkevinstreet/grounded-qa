// ########################################################################
// #                frontend/src/components/AuditTable.tsx                #
// ########################################################################
/**
 * Author:            Kevin Street
 * Created on:        2026-10-29
 * Last modified on:  2026-10-29
 *
 * The audit log table: every change to the sources, newest first, with
 * its time, the source, the SHA-256 of its text and the request that
 * made it.
 */

// ########################################################################
// #                               Imports                                #
// ########################################################################
// Local
import { CONFIG } from '../config';
import { required } from '../lib/required';
import type { AuditEntry } from '../types';

// ########################################################################
// #                           Global constants                           #
// ########################################################################
// log.debug('Takes how many characters of a hash are shown from the config')
const HASH_CHARS = CONFIG.web.hash_chars;

// ########################################################################
// #                             Audit table                              #
// ########################################################################
// log.debug('Defines the audit table')
/**
 * Renders the audit log as a table, or says nothing has changed yet.
 *
 * @param props - The component's props.
 * @param props.entries - The changes to show, newest first. Required.
 * @returns The table, or the empty state.
 */
export function AuditTable({
  entries = null,
}: { entries?: AuditEntry[] | null } = {}): React.JSX.Element {
  // log.debug('Takes the entries, which the caller must give')
  entries = required({ entries });
  // log.debug('Says so plainly when nothing has changed yet')
  if (entries.length === 0) {
    // log.debug('Returns the empty state')
    return (
      <p className="gq-reader__empty">No changes yet. Each add or remove will appear here.</p>
    );
  }
  // log.debug('Returns the table')
  return (
    <table className="gq-table">
      <caption className="gq-visually-hidden">Changes to the approved sources</caption>
      <thead>
        <tr>
          <th scope="col">When (UTC)</th>
          <th scope="col">Change</th>
          <th scope="col">Source</th>
          <th scope="col">SHA-256</th>
          <th scope="col">Request</th>
        </tr>
      </thead>
      <tbody>
        {entries.map((entry) => (
          <tr key={entry.id}>
            <td>{entry.at.replace('T', ' ').replace('+00:00', '')}</td>
            <td>{entry.action === 'add' ? 'Added' : 'Removed'}</td>
            <td>{entry.source_id}</td>
            <td>
              <code title={entry.sha256}>{entry.sha256.slice(0, HASH_CHARS)}</code>
            </td>
            <td>
              <code>{entry.request_id}</code>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
