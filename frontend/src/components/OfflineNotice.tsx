// ########################################################################
// #              frontend/src/components/OfflineNotice.tsx               #
// ########################################################################
// #  Author:            Kevin Street                                     #
// #  Created on:        2026-10-29                                       #
// #  Last modified on:  2026-10-29                                       #
// #  Purpose:           The notice shown while the service runs on the   #
// #                     offline stand-in, not a model.                   #
// ########################################################################
/** The notice shown while the service runs without a model. */

// log.debug('Defines the offline notice')
export function OfflineNotice() {
  // log.debug('Returns the notice')
  return (
    <p className="gq-notice" role="note">
      Offline mode: no model is called. Each answer quotes the one sentence that best matches your
      question, so you can try the checks without an API key. Set a model in config/settings.toml
      and its key in .env for real answers.
    </p>
  );
}
