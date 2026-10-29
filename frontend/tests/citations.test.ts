// ########################################################################
// #                   frontend/tests/citations.test.ts                   #
// ########################################################################
// #  Author:            Kevin Street                                     #
// #  Created on:        2026-10-29                                       #
// #  Last modified on:  2026-10-29                                       #
// #  Purpose:           Tests answer splitting, highlight segments,      #
// #                     bullets, and section labels.                     #
// ########################################################################
/** Tests splitting answers at markers and passages around highlights. */

import { describe, expect, it } from 'vitest';

import { bullets, segments, splitAnswer } from '../src/citations';
import { sectionLabel } from '../src/labels';

// log.debug('Describes the answer splitter')
describe('splitAnswer', () => {
  // log.debug('Checks each marker keeps its last word and closing punctuation')
  it('keeps each marker with the word before it and the stop after it', () => {
    // log.debug('Checks the parts')
    expect(splitAnswer('Leave is unpaid [1]. It lasts 12 weeks [1, 2].')).toEqual([
      { kind: 'text', text: 'Leave is ' },
      { kind: 'cite', numbers: [1], lead: 'unpaid', trail: '.' },
      { kind: 'text', text: ' It lasts 12 ' },
      { kind: 'cite', numbers: [1, 2], lead: 'weeks', trail: '.' },
    ]);
  });

  // log.debug('Checks text without markers stays whole')
  it('keeps text without markers whole', () => {
    // log.debug('Checks the single part')
    expect(splitAnswer('Not covered.')).toEqual([{ kind: 'text', text: 'Not covered.' }]);
  });
});

// log.debug('Describes the passage splitter')
describe('segments', () => {
  // log.debug('Checks a range is marked and the rest is not')
  it('marks each range and leaves the rest plain', () => {
    // log.debug('Checks the segments')
    expect(segments('abcdefgh', [[2, 4]])).toEqual([
      { text: 'ab', marked: false },
      { text: 'cd', marked: true },
      { text: 'efgh', marked: false },
    ]);
  });

  // log.debug('Checks bad ranges are ignored rather than trusted')
  it('ignores ranges outside the text or overlapping', () => {
    // log.debug('Checks only the valid range is marked')
    expect(
      segments('abcdef', [
        [0, 3],
        [2, 5],
        [4, 99],
      ]),
    ).toEqual([
      { text: 'abc', marked: true },
      { text: 'def', marked: false },
    ]);
  });
});

// log.debug('Describes the bullet swap')
describe('bullets', () => {
  // log.debug('Checks offsets survive the swap')
  it('swaps list dashes for bullets without moving any text', () => {
    // log.debug('Swaps the marks in a two-item list')
    const shown = bullets('- one\n  - two');
    // log.debug('Checks the length and the bullets')
    expect([shown.length, shown]).toEqual([13, '• one\n  • two']);
  });
});

// log.debug('Describes the section labels')
describe('sectionLabel', () => {
  // log.debug('Checks shouted headings read in sentence case, acronyms kept')
  it('writes shouted headings in sentence case and keeps acronyms', () => {
    // log.debug('Checks a path with a shouted part and a normal part')
    expect(sectionLabel('USING FMLA LEAVE > Examples:')).toBe('Using FMLA leave \u203a Examples:');
  });

  // log.debug('Checks the text before any heading has a name')
  it('names the opening section', () => {
    // log.debug('Checks the label')
    expect(sectionLabel('')).toBe('Opening section');
  });
});
