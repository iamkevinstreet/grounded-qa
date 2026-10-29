// ########################################################################
// #                        frontend/src/config.ts                        #
// ########################################################################
// #  Author:            Kevin Street                                     #
// #  Created on:        2026-10-29                                       #
// #  Last modified on:  2026-10-29                                       #
// #  Purpose:           Frontend settings in one place: the API address, #
// #                     question limits, examples, acronyms.             #
// ########################################################################
/** Frontend settings: the only module that reads the build environment. */

// log.debug('Reads the API address; by default this origin, through the dev proxy')
export const API_BASE: string = import.meta.env.VITE_API_BASE ?? '/api/v1';
// log.debug('Sets the shortest question the API accepts')
export const MIN_QUESTION_CHARS = 3;
// log.debug('Sets the longest question the API accepts')
export const MAX_QUESTION_CHARS = 1000;
// log.debug('Lists the example questions the ask page offers')
export const EXAMPLES: readonly string[] = [
  'How many weeks of FMLA leave can I take?',
  'Can my supervisor call my doctor about my leave?',
  'Do short breaks count as hours worked?',
  'Can I take FMLA leave to care for my mother-in-law?',
];
// log.debug('Lists acronyms a heading keeps in capitals')
export const ACRONYMS: readonly string[] = [
  'FMLA',
  'FLSA',
  'ADA',
  'USERRA',
  'PUMP',
  'U.S.',
  'PTO',
];
// log.debug('Names the provider that means the offline stand-in')
export const OFFLINE_PROVIDER = 'fake';
