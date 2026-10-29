// ########################################################################
// #                frontend/src/components/AnswerText.tsx                #
// ########################################################################
/**
 * Author:            Kevin Street
 * Created on:        2026-10-29
 * Last modified on:  2026-10-29
 *
 * The answer text, with each citation marker a button that shows its
 * source on the sheet beside it.
 */

// ########################################################################
// #                               Imports                                #
// ########################################################################
// Third-party
import { Fragment } from 'react';

// Local
import { splitAnswer } from '../citations';
import { required } from '../lib/required';

// ########################################################################
// #                             Answer text                              #
// ########################################################################
interface Props {
  text?: string | null;
  selected?: number | null;
  onSelect?: ((n: number) => void) | null;
}

// log.debug('Defines the answer text with its markers')
/**
 * Renders the answer, with each citation marker a button.
 *
 * @param props - The component's props.
 * @param props.text - The answer, with its [n] markers. Required.
 * @param props.selected - The number of the citation the sheet shows.
 *   Required.
 * @param props.onSelect - Shows a citation, by its number. Required.
 * @returns The answer as a paragraph, each marker pressed when its
 *   citation is the one shown.
 */
export function AnswerText({
  text = null,
  selected = null,
  onSelect = null,
}: Props = {}): React.JSX.Element {
  // log.debug('Takes the text, which the caller must give')
  text = required({ text });
  // log.debug('Takes the citation shown, which the caller must give')
  selected = required({ selected });
  // log.debug('Takes what choosing a marker does, which the caller must give')
  onSelect = required({ onSelect });
  // log.debug('Returns the text with a button for each marker')
  return (
    <p className="gq-answer__text">
      {splitAnswer(text).map((part, index) =>
        part.kind === 'text' ? (
          <Fragment key={index}>{part.text}</Fragment>
        ) : (
          <span key={index} className="gq-markers">
            {part.lead}
            {part.numbers.map((n) => (
              <button
                key={n}
                className="gq-marker"
                type="button"
                aria-pressed={n === selected}
                aria-label={`Show source ${n}`}
                onClick={() => onSelect(n)}
              >
                {n}
              </button>
            ))}
            {part.trail}
          </span>
        ),
      )}
    </p>
  );
}
