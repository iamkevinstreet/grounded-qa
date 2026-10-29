// ########################################################################
// #               frontend/src/components/Highlighted.tsx                #
// ########################################################################
/**
 * Author:            Kevin Street
 * Created on:        2026-10-29
 * Last modified on:  2026-10-29
 *
 * A passage with its checked quote marked, the way a highlighter would
 * mark it.
 */

// ########################################################################
// #                               Imports                                #
// ########################################################################
// Third-party
import { Fragment } from 'react';

// Local
import { bullets, segments } from '../citations';
import { required } from '../lib/required';
import type { Span } from '../types';

// ########################################################################
// #                         Highlighted passage                          #
// ########################################################################
interface Props {
  text?: string | null;
  spans?: readonly Span[] | null;
}

// log.debug('Defines the highlighted passage')
/**
 * Renders a passage with its checked quote marked.
 *
 * @param props - The component's props.
 * @param props.text - The passage. Required.
 * @param props.spans - The quote's ranges in the passage. Required.
 * @returns The passage, each quoted range in a mark.
 */
export function Highlighted({ text = null, spans = null }: Props = {}): React.JSX.Element {
  // log.debug('Takes the text, which the caller must give')
  text = required({ text });
  // log.debug('Takes the ranges, which the caller must give')
  spans = required({ spans });
  // log.debug('Returns the passage with each quoted range in a mark')
  return (
    <p className="gq-passage">
      {segments(bullets(text), spans).map((segment, index) =>
        segment.marked ? (
          <mark key={index} className="gq-mark">
            {segment.text}
          </mark>
        ) : (
          <Fragment key={index}>{segment.text}</Fragment>
        ),
      )}
    </p>
  );
}
