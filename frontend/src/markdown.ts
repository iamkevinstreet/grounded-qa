// ########################################################################
// #                       frontend/src/markdown.ts                       #
// ########################################################################
/**
 * Author:            Kevin Street
 * Created on:        2026-10-29
 * Last modified on:  2026-10-29
 *
 * Reads a source document's Markdown into the blocks the reader renders
 * as elements: headings, paragraphs, lists and tables.
 */

// ########################################################################
// #                               Imports                                #
// ########################################################################
// Local
import { required } from './lib/required';

// ########################################################################
// #                           Local constants                            #
// ########################################################################
// log.debug('Matches a heading block; captures its marks and text')
const HEADING = /^(#{1,6})\s+(.+)$/;
// log.debug('Matches a list item line; captures its indent and text')
const ITEM = /^(\s*)- (.*)$/;
// log.debug('Sets the spaces one level of list nesting uses')
const INDENT = 2;
// log.debug('Sets the character that starts and divides a table row')
const BAR = '|';

// ########################################################################
// #                           Markdown blocks                            #
// ########################################################################
export type Block =
  | { kind: 'heading'; level: number; text: string }
  | { kind: 'paragraph'; text: string }
  | { kind: 'list'; items: { depth: number; text: string }[] }
  | { kind: 'table'; rows: string[][] };

// log.debug('Defines how a document becomes blocks')
/**
 * Reads a document into its blocks.
 *
 * @param body - The document's text, as Markdown. Required.
 * @returns The blocks in order, empty ones left out.
 */
export function parseBlocks(body: string | null = null): Block[] {
  // log.debug('Takes the body, which the caller must give')
  body = required({ body });
  // log.debug('Splits at blank lines and reads each block')
  return body
    .split(/\n{2,}/)
    .map((block) => block.trimEnd())
    .filter((block) => block.trim() !== '')
    .map(toBlock);
}

// log.debug('Defines how one block is read')
/**
 * Reads one block of a document.
 *
 * @param block - The block's text, without the blank lines around it.
 *   Required.
 * @returns A heading, a list, a table, or else a paragraph.
 */
function toBlock(block: string | null = null): Block {
  // log.debug('Takes the block, which the caller must give')
  block = required({ block });
  // log.debug('Reads a heading')
  const heading = HEADING.exec(block.trim());
  // log.debug('Returns a heading block')
  if (heading?.[1] && heading[2]) {
    // log.debug('Returns its level and text')
    return { kind: 'heading', level: heading[1].length, text: heading[2] };
  }
  // log.debug('Splits the block into lines')
  const lines = block.split('\n');
  // log.debug('Reads a block where every line is a list item as a list')
  if (lines.every((line) => ITEM.test(line))) {
    // log.debug('Returns each item with its nesting depth')
    return { kind: 'list', items: lines.map(item) };
  }
  // log.debug('Reads a block where every line starts with a bar as a table')
  if (lines.every((line) => line.trim().startsWith(BAR))) {
    // log.debug('Returns each row cell by cell')
    return {
      kind: 'table',
      rows: lines.map((line) =>
        line
          .trim()
          .split(BAR)
          .slice(1, -1)
          .map((cell) => cell.trim()),
      ),
    };
  }
  // log.debug('Returns anything else as a paragraph')
  return { kind: 'paragraph', text: block.trim() };
}

// log.debug('Defines how one list line is read')
/**
 * Reads one line of a list.
 *
 * @param line - The line, with its indent and dash. Required.
 * @returns The item's nesting depth and its text.
 */
function item(line: string | null = null): { depth: number; text: string } {
  // log.debug('Takes the line, which the caller must give')
  line = required({ line });
  // log.debug('Matches the line')
  const match = ITEM.exec(line);
  // log.debug('Returns its depth from the indent, and its text')
  return { depth: Math.floor((match?.[1]?.length ?? 0) / INDENT), text: match?.[2] ?? line };
}
