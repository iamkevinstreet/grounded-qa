// ########################################################################
// #                       frontend/src/approver.ts                       #
// ########################################################################
/**
 * Author:            Kevin Street
 * Created on:        2026-10-29
 * Last modified on:  2026-10-29
 *
 * The approver's session: the token, held in memory only, and what the
 * page shows. Unlocking reads the audit log with the token; adding or
 * removing a source then refreshes the source list and the audit log.
 */

// ########################################################################
// #                               Imports                                #
// ########################################################################
// Third-party
import { useState, type SubmitEvent } from 'react';

// Local
import { api, describeError } from './api';
import { required } from './lib/required';
import type { AuditEntry, NewSource } from './types';

// ########################################################################
// #                           Approver session                           #
// ########################################################################
export interface Approver {
  token: string;
  setToken: (token: string) => void;
  unlocked: boolean;
  setUnlocked: (unlocked: boolean) => void;
  audit: AuditEntry[];
  setAudit: (entries: AuditEntry[]) => void;
  message: string | null;
  setMessage: (message: string | null) => void;
  confirming: string | null;
  setConfirming: (id: string | null) => void;
  onChanged: () => void;
}

// log.debug('Defines the hook that keeps the approver session')
/**
 * Keeps the approver page's token, audit log and messages, in memory.
 *
 * @param onChanged - Reloads the sources after a change. Required.
 * @returns The session, with a setter for each part.
 */
export function useApprover(onChanged: (() => void) | null = null): Approver {
  // log.debug('Takes what a change reloads, which the caller must give')
  onChanged = required({ onChanged });
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
  // log.debug('Returns the session')
  return {
    token,
    setToken,
    unlocked,
    setUnlocked,
    audit,
    setAudit,
    message,
    setMessage,
    confirming,
    setConfirming,
    onChanged,
  };
}

// log.debug('Defines unlocking: the audit log is read with the token')
/**
 * Reads the audit log with the token, which proves the token works.
 *
 * @param approver - The approver session. Required.
 * @param event - The token form's submit event. Required.
 */
export async function unlock(
  approver: Approver | null = null,
  event: SubmitEvent<HTMLFormElement> | null = null,
): Promise<void> {
  // log.debug('Takes the session, which the caller must give')
  approver = required({ approver });
  // log.debug('Takes the event, which the caller must give')
  event = required({ event });
  // log.debug('Stops the browser from reloading the page')
  event.preventDefault();
  // log.debug('Reads the audit log, which proves the token works')
  try {
    // log.debug('Shows the audit log')
    approver.setAudit(await api.audit(approver.token));
    // log.debug('Opens the approver tools')
    approver.setUnlocked(true);
    // log.debug('Clears any earlier problem')
    approver.setMessage(null);
  } catch (error) {
    // log.debug('Explains why the token was refused')
    approver.setMessage(describeError(error));
  }
}

// log.debug('Defines adding a source, then refreshing everything it touches')
/**
 * Adds a source, then refreshes the source list and the audit log.
 *
 * @param approver - The approver session. Required.
 * @param source - The source the approver submitted. Required.
 */
export async function addSource(
  approver: Approver | null = null,
  source: NewSource | null = null,
): Promise<void> {
  // log.debug('Takes the session, which the caller must give')
  approver = required({ approver });
  // log.debug('Takes the source, which the caller must give')
  source = required({ source });
  // log.debug('Adds it; a refusal is shown, not thrown')
  try {
    // log.debug('Sends the new source')
    await api.addSource(approver.token, source);
    // log.debug('Confirms the change')
    approver.setMessage(`Added ${source.id}.`);
    // log.debug('Refreshes the source list')
    approver.onChanged();
    // log.debug('Refreshes the audit log')
    approver.setAudit(await api.audit(approver.token));
  } catch (error) {
    // log.debug('Shows what the service refused and why')
    approver.setMessage(describeError(error));
  }
}

// log.debug('Defines removing a source after a second click')
/**
 * Removes a source on its second click, then refreshes the lists.
 *
 * @param approver - The approver session. Required.
 * @param id - The id of the source to remove. Required.
 */
export async function removeSource(
  approver: Approver | null = null,
  id: string | null = null,
): Promise<void> {
  // log.debug('Takes the session, which the caller must give')
  approver = required({ approver });
  // log.debug('Takes the id, which the caller must give')
  id = required({ id });
  // log.debug('Asks for a second click first')
  if (approver.confirming !== id) {
    // log.debug('Waits for the confirming click')
    approver.setConfirming(id);
    // log.debug('Stops here until then')
    return;
  }
  // log.debug('Removes it; a refusal is shown, not thrown')
  try {
    // log.debug('Sends the removal')
    await api.removeSource(approver.token, id);
    // log.debug('Confirms the change')
    approver.setMessage(`Removed ${id}.`);
    // log.debug('Refreshes the source list')
    approver.onChanged();
    // log.debug('Refreshes the audit log')
    approver.setAudit(await api.audit(approver.token));
  } catch (error) {
    // log.debug('Shows what went wrong')
    approver.setMessage(describeError(error));
  } finally {
    // log.debug('Clears the pending confirmation')
    approver.setConfirming(null);
  }
}
