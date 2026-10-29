// ########################################################################
// #                 frontend/src/pages/ApproverPage.tsx                  #
// ########################################################################
/**
 * Author:            Kevin Street
 * Created on:        2026-10-29
 * Last modified on:  2026-10-29
 *
 * The approver page: unlock with the token, add or remove sources, read
 * the audit log.
 */

// ########################################################################
// #                               Imports                                #
// ########################################################################
// Local
import { addSource, removeSource, unlock, useApprover } from '../approver';
import { ApproverTools } from '../components/ApproverTools';
import { TokenForm } from '../components/TokenForm';
import { required } from '../lib/required';
import type { Health, SourceSummary } from '../types';

// ########################################################################
// #                            Approver page                             #
// ########################################################################
interface Props {
  health?: Health | null;
  sources?: SourceSummary[] | null;
  onChanged?: (() => void) | null;
}

// log.debug('Defines the approver page')
/**
 * Renders the approver page, or says approver changes are off.
 *
 * @param props - The component's props.
 * @param props.health - The service's health report; null until it
 *   loads.
 * @param props.sources - The approved sources. Required.
 * @param props.onChanged - Reloads the sources after a change. Required.
 * @returns The page.
 */
export function ApproverPage({
  health = null,
  sources = null,
  onChanged = null,
}: Props = {}): React.JSX.Element {
  // log.debug('Takes the sources, which the caller must give')
  sources = required({ sources });
  // log.debug('Keeps the token and what the page shows, in memory only')
  const approver = useApprover(onChanged);

  // log.debug('Says so plainly when the server has approver changes off')
  if (health && !health.admin) {
    // log.debug('Returns the explanation and how to turn them on')
    return (
      <div className="gq-page">
        <h1 className="gq-intro__title">Approver</h1>
        <p className="gq-intro__lede">
          Approver changes are off on this server. Set APPROVER_TOKEN in config/.env (at least 32
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
      {approver.message && (
        <p className="gq-status" role="status">
          {approver.message}
        </p>
      )}
      {!approver.unlocked && (
        <TokenForm
          token={approver.token}
          onChange={approver.setToken}
          onUnlock={(event) => void unlock(approver, event)}
        />
      )}
      {approver.unlocked && (
        <ApproverTools
          sources={sources}
          audit={approver.audit}
          confirming={approver.confirming}
          onAdd={(source) => addSource(approver, source)}
          onRemove={(id) => void removeSource(approver, id)}
        />
      )}
    </div>
  );
}
