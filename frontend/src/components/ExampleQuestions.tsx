// ########################################################################
// #             frontend/src/components/ExampleQuestions.tsx             #
// ########################################################################
/**
 * Author:            Kevin Street
 * Created on:        2026-10-29
 * Last modified on:  2026-10-29
 *
 * The example questions under the question box; choosing one asks it.
 */

// ########################################################################
// #                               Imports                                #
// ########################################################################
// Local
import { required } from '../lib/required';

// ########################################################################
// #                           Local constants                            #
// ########################################################################
// log.debug('Lists the example questions the ask page offers')
const EXAMPLES: readonly string[] = [
  'How many weeks of FMLA leave can I take?',
  'Can my supervisor call my doctor about my leave?',
  'Do short breaks count as hours worked?',
  'Can I take FMLA leave to care for my mother-in-law?',
];

// ########################################################################
// #                          Example questions                           #
// ########################################################################
interface Props {
  busy?: boolean;
  onChoose?: ((example: string) => void) | null;
}

// log.debug('Defines the example questions')
/**
 * Renders the example questions as buttons that ask them.
 *
 * @param props - The component's props.
 * @param props.busy - Whether a question is being answered, which
 *   disables the examples.
 * @param props.onChoose - Asks an example, given its text. Required.
 * @returns The examples, under their label.
 */
export function ExampleQuestions({
  busy = false,
  onChoose = null,
}: Props = {}): React.JSX.Element {
  // log.debug('Takes what choosing an example does, which the caller must give')
  onChoose = required({ onChoose });
  // log.debug('Returns the examples')
  return (
    <div className="gq-examples">
      <p className="gq-examples__label" id="examples">
        Or try one of these:
      </p>
      <ul className="gq-examples__list" aria-labelledby="examples">
        {EXAMPLES.map((example) => (
          <li key={example}>
            <button
              className="gq-chip"
              type="button"
              disabled={busy}
              onClick={() => onChoose(example)}
            >
              {example}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
