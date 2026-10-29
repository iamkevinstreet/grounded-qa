// ########################################################################
// #               frontend/src/components/Highlighted.tsx                #
// ########################################################################
// #  Author:            Kevin Street                                     #
// #  Created on:        2026-10-29                                       #
// #  Last modified on:  2026-10-29                                       #
// #  Purpose:           A passage with its checked quote marked, the way #
// #                     a highlighter would mark it.                     #
// ########################################################################
/** A passage with its checked quote marked, as the highlighter would. */

import { Fragment } from 'react';

import { bullets, segments } from '../citations';
import type { Span } from '../types';

interface Props {
  text: string;
  spans: readonly Span[];
}

// log.debug('Defines the highlighted passage')
export function Highlighted({ text, spans }: Props) {
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
