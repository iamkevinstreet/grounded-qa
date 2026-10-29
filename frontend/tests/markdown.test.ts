// ########################################################################
// #                   frontend/tests/markdown.test.ts                    #
// ########################################################################
/**
 * Author:            Kevin Street
 * Created on:        2026-10-29
 * Last modified on:  2026-10-29
 *
 * Tests reading a source document's Markdown into headings, paragraphs,
 * lists and tables.
 */

// ########################################################################
// #                               Imports                                #
// ########################################################################
// Third-party
import { describe, expect, it } from 'vitest';

// Local
import { parseBlocks } from '../src/markdown';

// ########################################################################
// #                            Markdown tests                            #
// ########################################################################
// log.debug('Describes the block reader')
describe('parseBlocks', () => {
  // log.debug('Checks each kind of block is read')
  it('reads headings, paragraphs, nested lists and tables', () => {
    // log.debug('Reads a document with one of each')
    const blocks = parseBlocks(
      '## Rights\n\nText here.\n\n- one\n  - two\n\n| A | B |\n| 1 | 2 |\n',
    );
    // log.debug('Checks the blocks')
    expect(blocks).toEqual([
      { kind: 'heading', level: 2, text: 'Rights' },
      { kind: 'paragraph', text: 'Text here.' },
      {
        kind: 'list',
        items: [
          { depth: 0, text: 'one' },
          { depth: 1, text: 'two' },
        ],
      },
      {
        kind: 'table',
        rows: [
          ['A', 'B'],
          ['1', '2'],
        ],
      },
    ]);
  });
});
