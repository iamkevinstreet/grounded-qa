// ########################################################################
// #                frontend/src/components/SourceText.tsx                #
// ########################################################################
/**
 * Author:            Kevin Street
 * Created on:        2026-10-29
 * Last modified on:  2026-10-29
 *
 * A whole source document, rendered from its Markdown blocks.
 */

// ########################################################################
// #                               Imports                                #
// ########################################################################
// Local
import { required } from '../lib/required';
import { parseBlocks, type Block } from '../markdown';

// ########################################################################
// #                           Source document                            #
// ########################################################################
// log.debug('Defines how one block is rendered')
/**
 * Renders one block of a document as its element.
 *
 * @param block - The block. Required.
 * @param index - Its position in the document, used as its key. Required.
 * @returns A heading, list, table or paragraph.
 */
function render(block: Block | null = null, index: number | null = null): React.JSX.Element {
  // log.debug('Takes the block, which the caller must give')
  block = required({ block });
  // log.debug('Takes the position, which the caller must give')
  index = required({ index });
  // log.debug('Chooses the element for the block kind')
  switch (block.kind) {
    case 'heading':
      // log.debug('Returns a heading two levels down from the page title')
      return block.level <= 2 ? (
        <h3 key={index}>{block.text}</h3>
      ) : (
        <h4 key={index}>{block.text}</h4>
      );
    case 'list':
      // log.debug('Returns a list, nested items indented')
      return (
        <ul key={index}>
          {block.items.map((item, n) => (
            <li key={n} className={item.depth > 0 ? 'gq-doc__nested' : undefined}>
              {item.text}
            </li>
          ))}
        </ul>
      );
    case 'table':
      // log.debug('Returns a table, its first row as the header')
      return (
        <div key={index} className="gq-doc__table">
          <table>
            <tbody>
              {block.rows.map((row, r) => (
                <tr key={r}>
                  {row.map((cell, c) =>
                    r === 0 ? <th key={c}>{cell}</th> : <td key={c}>{cell}</td>,
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    case 'paragraph':
      // log.debug('Returns a paragraph')
      return <p key={index}>{block.text}</p>;
  }
}

// log.debug('Defines the document view')
/**
 * Renders a whole source document from its Markdown.
 *
 * @param props - The component's props.
 * @param props.body - The document's text, as Markdown. Required.
 * @returns The document's blocks, in order.
 */
export function SourceText({ body = null }: { body?: string | null } = {}): React.JSX.Element {
  // log.debug('Takes the text, which the caller must give')
  body = required({ body });
  // log.debug('Returns every block of the document')
  return <div className="gq-doc">{parseBlocks(body).map(render)}</div>;
}
