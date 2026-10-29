// ########################################################################
// #                        frontend/src/labels.ts                        #
// ########################################################################
// #  Author:            Kevin Street                                     #
// #  Created on:        2026-10-29                                       #
// #  Last modified on:  2026-10-29                                       #
// #  Purpose:           Display labels: a passage's heading path in      #
// #                     sentence case, with acronyms kept.               #
// ########################################################################
/** Display labels: a passage's heading path, written in sentence case. */

import { ACRONYMS } from './config';

// log.debug('Sets the text between the parts of a heading path')
const PATH_SEP = ' > ';
// log.debug('Sets the text shown between parts of a heading path')
const SHOWN_SEP = ' \u203a ';
// log.debug('Matches the letters a word must keep in capitals')
const LETTERS = /[A-Za-z.]+/;

// log.debug('Defines the label for a heading path')
export function sectionLabel(section: string): string {
  // log.debug('Names the text before the first heading')
  if (section === '') {
    // log.debug('Returns the opening label')
    return 'Opening section';
  }
  // log.debug('Writes each shouted heading in sentence case')
  return section
    .split(PATH_SEP)
    .map((part) => (part === part.toUpperCase() ? sentenceCase(part) : part))
    .join(SHOWN_SEP);
}

// log.debug('Defines sentence case that keeps acronyms such as FMLA')
export function sentenceCase(text: string): string {
  // log.debug('Lowercases each word unless it is a known acronym')
  const words = text
    .split(' ')
    .map((word) => (ACRONYMS.includes(LETTERS.exec(word)?.[0] ?? '') ? word : word.toLowerCase()));
  // log.debug('Joins the words back together')
  const joined = words.join(' ');
  // log.debug('Capitalises the first letter')
  return joined.charAt(0).toUpperCase() + joined.slice(1);
}
