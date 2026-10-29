// ########################################################################
// #                 frontend/src/pages/ApproverPage.tsx                  #
// ########################################################################
// #  Author:            Kevin Street                                     #
// #  Created on:        2026-10-29                                       #
// #  Last modified on:  2026-10-29                                       #
// #  Purpose:           The approver page: unlock with the token, add or #
// #                     remove sources, read the audit log.              #
// ########################################################################
/** The approver page: unlock with the token, add or remove sources, read the log. */

import { useState, type SubmitEvent } from 'react';

import { api, describeError } from '../api';
import { AddSourceForm } from '../components/AddSourceForm';
import { AuditTable } from '../components/AuditTable';
import type { AuditEntry, Health, NewSource, SourceSummary } from '../types';

interface Props {
  health: Health | null;
  sources: SourceSummary[];
  onChanged: () => void;
}

// log.debug('Defines the approver page')
export function ApproverPage({ health, sources, onChanged }: Props) {
  // log.debug('Keeps the token in memory only, never in storage')
  const [token, setToken] = useState('');
  // log.debug('Keeps whether the token has been accepted')
  const [unlocked, setUnlocked] = useState(false);
  // log.debug('Keeps the audit log')
  const [audit, setAudit] = useState<AuditEntry[]>([]);
  // log.debug('Keeps the last result or problem to show')
  const [message, setMessage] = useState<string | null>(null);
  // log.debug('Keeps which source is waiting for a second click to remove')
  const [confirming, setConfirming] = useState<string | null>(null);

  // log.debug('Defines unlocking: the audit log is read with the token')
  async function unlock(event: SubmitEvent<HTMLFormElement>): Promise<void> {
    // log.debug('Stops the browser from reloading the page')
    event.preventDefault();
    // log.debug('Reads the audit log, which proves the token works')
    try {
      // log.debug('Shows the audit log')
      setAudit(await api.audit(token));
      // log.debug('Opens the approver tools')
      setUnlocked(true);
      // log.debug('Clears any earlier problem')
      setMessage(null);
    } catch (error) {
      // log.debug('Explains why the token was refused')
      setMessage(describeError(error));
    }
  }

  // log.debug('Defines adding a source, then refreshing everything it touches')
  async function add(source: NewSource): Promise<void> {
    // log.debug('Adds it; a refusal is shown, not thrown')
    try {
      // log.debug('Sends the new source')
      await api.addSource(token, source);
      // log.debug('Confirms the change')
      setMessage(`Added ${source.id}.`);
      // log.debug('Refreshes the source list')
      onChanged();
      // log.debug('Refreshes the audit log')
      setAudit(await api.audit(token));
    } catch (error) {
      // log.debug('Shows what the service refused and why')
      setMessage(describeError(error));
    }
  }

  // log.debug('Defines removing a source after a second click')
  async function remove(id: string): Promise<void> {
    // log.debug('Asks for a second click first')
    if (confirming !== id) {
      // log.debug('Waits for the confirming click')
      setConfirming(id);
      // log.debug('Stops here until then')
      return;
    }
    // log.debug('Removes it; a refusal is shown, not thrown')
    try {
      // log.debug('Sends the removal')
      await api.removeSource(token, id);
      // log.debug('Confirms the change')
      setMessage(`Removed ${id}.`);
      // log.debug('Refreshes the source list')
      onChanged();
      // log.debug('Refreshes the audit log')
      setAudit(await api.audit(token));
    } catch (error) {
      // log.debug('Shows what went wrong')
      setMessage(describeError(error));
    } finally {
      // log.debug('Clears the pending confirmation')
      setConfirming(null);
    }
  }

  // log.debug('Says so plainly when the server has approver changes off')
  if (health && !health.admin) {
    // log.debug('Returns the explanation and how to turn them on')
    return (
      <div className="gq-page">
        <h1 className="gq-intro__title">Approver</h1>
        <p className="gq-intro__lede">
          Approver changes are off on this server. Set APPROVER_TOKEN in .env (at least 32
          characters) and restart it to turn them on.
        </p>
      </div>
    );
  }
  // log.debug('Returns the page')
  return (
    <div className="gq-page">
      <h1 className="gq-intro__title">Approver</h1>
      <p className="gq-intro__lede">
        Only an approver can add or remove a source. Each change is recorded in the audit log with
        its time, the source, and the SHA-256 of its text.
      </p>
      {message && (
        <p className="gq-status" role="status">
          {message}
        </p>
      )}
      {!unlocked && (
        <form className="gq-form gq-form--inline" onSubmit={(event) => void unlock(event)}>
          <p className="gq-form__field">
            <label htmlFor="token">Approver token</label>
            <input
              id="token"
              type="password"
              autoComplete="off"
              required
              value={token}
              onChange={(event) => setToken(event.target.value)}
            />
          </p>
          <button className="gq-button" type="submit">
            Unlock
          </button>
        </form>
      )}
      {unlocked && (
        <div className="gq-approver">
          <section className="gq-approver__add" aria-labelledby="add-title">
            <h2 id="add-title" className="gq-section__title">
              Add a source
            </h2>
            <AddSourceForm onAdd={add} />
          </section>
          <section className="gq-approver__list" aria-labelledby="list-title">
            <h2 id="list-title" className="gq-section__title">
              Sources
            </h2>
            <ul className="gq-admin-list">
              {sources.map((source) => (
                <li key={source.id}>
                  <span>{source.title}</span>
                  <button className="gq-link" type="button" onClick={() => void remove(source.id)}>
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
      )}
    </div>
  );
}
