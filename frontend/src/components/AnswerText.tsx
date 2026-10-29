// ########################################################################
// #                frontend/src/components/AnswerText.tsx                #
// ########################################################################
// #  Author:            Kevin Street                                     #
// #  Created on:        2026-10-29                                       #
// #  Last modified on:  2026-10-29                                       #
// #  Purpose:           The answer text, with each citation marker a     #
// #                     button that shows its source.                    #
// ########################################################################
/** The answer, with each citation marker as a button that shows its source. */

import { Fragment } from 'react';

import { splitAnswer } from '../citations';

interface Props {
  text: string;
  selected: number;
  onSelect: (n: number) => void;
}

// log.debug('Defines the answer text with its markers')
export function AnswerText({ text, selected, onSelect }: Props) {
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
