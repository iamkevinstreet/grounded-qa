// ########################################################################
// #                      frontend/src/citations.ts                       #
// ########################################################################
/**
 * Author:            Kevin Street
 * Created on:        2026-10-29
 * Last modified on:  2026-10-29
 *
 * Splits an answer at its citation markers, so each marker can become a
 * button, and a passage around its checked quotes, so each quote can be
 * highlighted.
 */

// ########################################################################
// #                               Imports                                #
// ########################################################################
// Local
import { required } from './lib/required';
import type { Span } from './types';

// ########################################################################
// #                           Local constants                            #
// ########################################################################
// log.debug('Matches a citation marker such as [1] or [1, 2]')
const MARKER = /\[(\d+(?:\s*,\s*\d+)*)\]/g;
// log.debug('Matches the last word of a text and the spaces after it')
const LAST_WORD = /(\S+)\s*$/;
// log.debug('Matches punctuation that closes a sentence after a marker')
const CLOSING = /^[.,;:!?)]+/;
// log.debug('Matches a list mark at the start of a line')
const LIST_MARK = /^(\s*)- /gm;

// ########################################################################
// #                        Markers and highlights                        #
// ########################################################################
export type AnswerPart =
  | { kind: 'text'; text: string }
  | { kind: 'cite'; numbers: number[]; lead: string; trail: string };

export interface Segment {
  text: string;
  marked: boolean;
}

// log.debug('Defines how an answer is split into text and markers')
/**
 * Splits an answer into its text and its citation markers.
 *
 * @param answer - The answer, with [n] markers. Required.
 * @returns The parts in order; each marker keeps the word before it and
 *   the punctuation after it, so they wrap together.
 */
export function splitAnswer(answer: string | null = null): AnswerPart[] {
  // log.debug('Takes the answer, which the caller must give')
  answer = required({ answer });
  // log.debug('Starts the parts')
  const parts: AnswerPart[] = [];
  // log.debug('Remembers where the last marker ended')
  let last = 0;
  // log.debug('Walks every marker in the answer')
  for (const match of answer.matchAll(MARKER)) {
    // log.debug('Takes the text between the last marker and this one')
    const before = answer.slice(last, match.index);
    // log.debug('Finds its last word, which stays on the line with the marker')
    const tail = LAST_WORD.exec(before);
    // log.debug('Finds closing punctuation right after the marker')
    const trail = CLOSING.exec(answer.slice(match.index + match[0].length))?.[0] ?? '';
    // log.debug('Adds the text before that last word')
    parts.push({ kind: 'text', text: before.slice(0, before.length - (tail?.[0].length ?? 0)) });
    // log.debug('Adds the marker with its numbers, last word and punctuation')
    parts.push({
      kind: 'cite',
      numbers: (match[1] ?? '').split(',').map((n) => Number(n)),
      lead: tail?.[1] ?? '',
      trail,
    });
    // log.debug('Moves past the marker and its punctuation')
    last = match.index + match[0].length + trail.length;
  }
  // log.debug('Adds the text after the last marker')
  parts.push({ kind: 'text', text: answer.slice(last) });
  // log.debug('Returns the parts, without empty text')
  return parts.filter((part) => part.kind === 'cite' || part.text !== '');
}

// log.debug('Defines how a passage is split around its highlighted ranges')
/**
 * Splits a passage around its highlighted ranges.
 *
 * @param text - The passage. Required.
 * @param spans - The ranges to highlight, as start and end offsets.
 *   Required.
 * @returns The plain and highlighted segments in order; ranges outside
 *   the text or overlapping one before them are left out.
 */
export function segments(
  text: string | null = null,
  spans: readonly Span[] | null = null,
): Segment[] {
  // log.debug('Takes the text, which the caller must give')
  text = required({ text });
  // log.debug('Takes the spans, which the caller must give')
  spans = required({ spans });
  // log.debug('Keeps the ranges inside the text, in order')
  const ordered = spans
    .filter(([start, end]) => start >= 0 && start < end && end <= text.length)
    .toSorted((x, y) => x[0] - y[0]);
  // log.debug('Starts the segments')
  const out: Segment[] = [];
  // log.debug('Remembers where the last range ended')
  let last = 0;
  // log.debug('Walks the ranges in order')
  for (const [start, end] of ordered) {
    // log.debug('Skips a range that overlaps the one before it')
    if (start < last) {
      // log.debug('Moves to the next range')
      continue;
    }
    // log.debug('Adds the plain text before the range')
    out.push({ text: text.slice(last, start), marked: false });
    // log.debug('Adds the highlighted range')
    out.push({ text: text.slice(start, end), marked: true });
    // log.debug('Moves past the range')
    last = end;
  }
  // log.debug('Adds the plain text after the last range')
  out.push({ text: text.slice(last), marked: false });
  // log.debug('Returns the segments, without empty ones')
  return out.filter((segment) => segment.text !== '');
}

// log.debug('Defines how list marks are shown as bullets, offsets unchanged')
/**
 * Shows a passage's list marks as bullets, with every offset unchanged.
 *
 * @param text - The passage. Required.
 * @returns The passage with each leading dash swapped for a bullet.
 */
export function bullets(text: string | null = null): string {
  // log.debug('Takes the text, which the caller must give')
  text = required({ text });
  // log.debug('Swaps each leading dash for a bullet of the same length')
  return text.replace(LIST_MARK, '$1• ');
}
