// ########################################################################
// #               frontend/src/components/CheckDetails.tsx               #
// ########################################################################
// #  Author:            Kevin Street                                     #
// #  Created on:        2026-10-29                                       #
// #  Last modified on:  2026-10-29                                       #
// #  Purpose:           How an answer was checked: quotes found,         #
// #                     passages searched, the model, the request id.    #
// ########################################################################
/** How an answer was checked: quotes found, passages searched, model, request. */

import type { Answer } from '../types';

// log.debug('Defines the check details')
export function CheckDetails({ answer }: { answer: Answer }) {
  // log.debug('Counts the quotes found and the ones removed')
  const found = answer.citations.length;
  // log.debug('Words the quote line')
  const quotes =
    answer.dropped > 0
      ? `${found} found word for word; ${answer.dropped} not found, so the claims they supported were removed`
      : `${found} of ${found} found word for word in their passages`;
  // log.debug('Returns the details, closed until asked for')
  return (
    <details className="gq-check">
      <summary>How this answer was checked</summary>
      <dl className="gq-check__list">
        <dt>Quotes</dt>
        <dd>{quotes}</dd>
        <dt>Search</dt>
        <dd>
          {answer.retrieved.length} passages shown to the model, by {answer.mode} search
        </dd>
        <dt>Model</dt>
        <dd>{answer.model ?? 'none called'}</dd>
        <dt>Request</dt>
        <dd>
          <code>{answer.request_id}</code>
        </dd>
      </dl>
    </details>
  );
}
