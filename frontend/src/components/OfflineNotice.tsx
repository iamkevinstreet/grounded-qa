// ########################################################################
// #              frontend/src/components/OfflineNotice.tsx               #
// ########################################################################
/**
 * Author:            Kevin Street
 * Created on:        2026-10-29
 * Last modified on:  2026-10-29
 *
 * The notice shown while the service runs on the offline stand-in, not
 * a model.
 */

// ########################################################################
// #                            Offline notice                            #
// ########################################################################
// log.debug('Defines the offline notice')
/**
 * Renders the notice shown while no model is called.
 *
 * @returns The notice, with how to set a model for real answers.
 */
export function OfflineNotice(): React.JSX.Element {
  // log.debug('Returns the notice')
  return (
    <p className="gq-notice" role="note">
      Offline mode: no model is called. Each answer quotes the one sentence that best matches your
      question, so you can try the checks without an API key. Set a model in config/config.toml and
      its key in config/.env for real answers.
    </p>
  );
}
