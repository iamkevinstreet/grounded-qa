// ########################################################################
// #                frontend/src/components/AuditTable.tsx                #
// ########################################################################
// #  Author:            Kevin Street                                     #
// #  Created on:        2026-10-29                                       #
// #  Last modified on:  2026-10-29                                       #
// #  Purpose:           The audit log table: every change to the         #
// #                     sources, newest first.                           #
// ########################################################################
/** The audit log: every change to the sources, newest first. */

import type { AuditEntry } from '../types';

// log.debug('Sets how many characters of a hash are shown')
const HASH_CHARS = 12;

// log.debug('Defines the audit table')
export function AuditTable({ entries }: { entries: AuditEntry[] }) {
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
