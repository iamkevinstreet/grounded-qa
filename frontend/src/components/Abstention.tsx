// ########################################################################
// #                frontend/src/components/Abstention.tsx                #
// ########################################################################
/**
 * Author:            Kevin Street
 * Created on:        2026-10-29
 * Last modified on:  2026-10-29
 *
 * What the ask page says when there is no checked answer: why, which
 * fact sheets were searched, and what the sources do cover.
 */

// ########################################################################
// #                               Imports                                #
// ########################################################################
// Local
import { required } from '../lib/required';
import type { Answer, Outcome } from '../types';

// ########################################################################
// #                           Local constants                            #
// ########################################################################
// log.debug('Sets the heading and explanation for each kind of abstention')
const COPY: Record<Exclude<Outcome, 'answered'>, { heading: string; body: string }> = {
  not_covered: {
    heading: 'The approved sources do not cover this',
    body: 'The model read the closest passages and found no answer in them, so it did not guess.',
  },
  no_passages: {
    heading: 'Nothing in the approved sources matches this',
    body: 'No passage shares any words with the question, so no model was asked.',
  },
  unverified: {
    heading: 'No answer: its quotes could not be checked',
    body: 'The draft cited text that is not in its sources, so it was withheld instead of shown.',
  },
};

// ########################################################################
// #                              Abstention                              #
// ########################################################################
interface Props {
  answer?: Answer | null;
  titles?: ReadonlyMap<string, string> | null;
}

// log.debug('Defines the abstention view')
/**
 * Renders what the page says when there is no checked answer.
 *
 * @param props - The component's props.
 * @param props.answer - The answer that ended in an abstention. Required.
 * @param props.titles - Each source's title by its id, to name the fact
 *   sheets searched. Required.
 * @returns Why there is no answer, the fact sheets searched, and what the
 *   sources cover.
 */
export function Abstention({ answer = null, titles = null }: Props = {}): React.JSX.Element {
  // log.debug('Takes the answer, which the caller must give')
  answer = required({ answer });
  // log.debug('Takes the titles, which the caller must give')
  titles = required({ titles });
  // log.debug('Picks the copy for this outcome')
  const copy = COPY[answer.outcome === 'answered' ? 'unverified' : answer.outcome];
  // log.debug('Lists the fact sheets that were searched, once each')
  const searched = [...new Set(answer.retrieved.map((r) => titles.get(r.doc_id) ?? r.doc_id))];
  // log.debug('Returns the explanation and what to try')
  return (
    <section className="gq-abstain" aria-labelledby="abstain-title">
      <h2 id="abstain-title" className="gq-abstain__title">
        {copy.heading}
      </h2>
      <p>{answer.outcome === 'not_covered' ? answer.answer : copy.body}</p>
      {searched.length > 0 && (
        <>
          <p className="gq-abstain__label">Fact sheets searched:</p>
          <ul className="gq-abstain__list">
            {searched.map((title) => (
              <li key={title}>{title}</li>
            ))}
          </ul>
        </>
      )}
      <p className="gq-abstain__hint">
        These sources cover FMLA leave, overtime, hours worked, recordkeeping, white-collar
        exemptions, retaliation, and breaks to pump at work.
      </p>
    </section>
  );
}
