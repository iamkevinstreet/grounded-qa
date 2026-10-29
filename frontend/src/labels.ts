// ########################################################################
// #                        frontend/src/labels.ts                        #
// ########################################################################
/**
 * Author:            Kevin Street
 * Created on:        2026-10-29
 * Last modified on:  2026-10-29
 *
 * Display labels: a passage's heading path, written in sentence case
 * where the source shouts it, with acronyms kept in capitals.
 */

// ########################################################################
// #                               Imports                                #
// ########################################################################
// Local
import { CONFIG } from './config';
import { required } from './lib/required';

// ########################################################################
// #                           Global constants                           #
// ########################################################################
// log.debug('Takes the text between the parts of a heading path from the config')
const PATH_SEP = CONFIG.retrieval.section_separator;

// ########################################################################
// #                           Local constants                            #
// ########################################################################
// log.debug('Lists acronyms a heading keeps in capitals')
const ACRONYMS: readonly string[] = ['FMLA', 'FLSA', 'ADA', 'USERRA', 'PUMP', 'U.S.', 'PTO'];
// log.debug('Sets the text shown between parts of a heading path')
const SHOWN_SEP = ' \u203a ';
// log.debug('Matches the letters a word must keep in capitals')
const LETTERS = /[A-Za-z.]+/;

// ########################################################################
// #                            Display labels                            #
// ########################################################################
// log.debug('Defines the label for a heading path')
/**
 * Returns the label for a passage's heading path.
 *
 * @param section - The heading path, its parts joined as the config
 *   sets; empty for the text before the first heading. Required.
 * @returns Each shouted heading in sentence case, the parts joined by a
 *   chevron, or Opening section for an empty path.
 */
export function sectionLabel(section: string | null = null): string {
  // log.debug('Takes the section, which the caller must give')
  section = required({ section });
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
/**
 * Writes a heading in sentence case, keeping acronyms such as FMLA.
 *
 * @param text - The heading. Required.
 * @returns The heading with only its first letter and its acronyms in
 *   capitals.
 */
export function sentenceCase(text: string | null = null): string {
  // log.debug('Takes the text, which the caller must give')
  text = required({ text });
  // log.debug('Lowercases each word unless it is a known acronym')
  const words = text
    .split(' ')
    .map((word) => (ACRONYMS.includes(LETTERS.exec(word)?.[0] ?? '') ? word : word.toLowerCase()));
  // log.debug('Joins the words back together')
  const joined = words.join(' ');
  // log.debug('Capitalises the first letter')
  return joined.charAt(0).toUpperCase() + joined.slice(1);
}
