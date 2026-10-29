// ########################################################################
// #               frontend/src/components/SourceFields.tsx               #
// ########################################################################
/**
 * Author:            Kevin Street
 * Created on:        2026-10-29
 * Last modified on:  2026-10-29
 *
 * The fields of the add-source form: a line for each part of a source's
 * provenance, with a hint, and a box for its text as Markdown.
 */

// ########################################################################
// #                               Imports                                #
// ########################################################################
// Local
import { required } from '../lib/required';
import type { NewSource } from '../types';

// ########################################################################
// #                           Local constants                            #
// ########################################################################
// log.debug('Lists the one-line fields with their labels and hints')
const FIELDS: readonly { name: Exclude<keyof NewSource, 'body'>; label: string; hint: string }[] =
  [
    {
      name: 'id',
      label: 'Id',
      hint: 'Lowercase letters, digits and dashes, such as dol-whd-fs28',
    },
    { name: 'title', label: 'Title', hint: 'As the publisher gives it' },
    { name: 'publisher', label: 'Publisher', hint: 'Who published it' },
    { name: 'source', label: 'Address', hint: 'The https address it was copied from' },
    { name: 'revised', label: 'Revised', hint: 'The revision date the document states' },
    { name: 'license', label: 'Licence', hint: 'The terms it may be used under' },
  ];

// ########################################################################
// #                            Source fields                             #
// ########################################################################
interface Props {
  values?: NewSource | null;
  onChange?: ((name: keyof NewSource, value: string) => void) | null;
}

// log.debug('Defines the fields of the add-source form')
/**
 * Renders a field for each part of a new source.
 *
 * @param props - The component's props.
 * @param props.values - The values typed so far. Required.
 * @param props.onChange - Takes a field's new value, given the field's
 *   name. Required.
 * @returns The fields, the text box last.
 */
export function SourceFields({ values = null, onChange = null }: Props = {}): React.JSX.Element {
  // log.debug('Takes the values, which the caller must give')
  values = required({ values });
  // log.debug('Takes what typing does, which the caller must give')
  onChange = required({ onChange });
  // log.debug('Returns the fields')
  return (
    <>
      {FIELDS.map((field) => (
        <p key={field.name} className="gq-form__field">
          <label htmlFor={`new-${field.name}`}>{field.label}</label>
          <input
            id={`new-${field.name}`}
            required
            value={values[field.name]}
            aria-describedby={`new-${field.name}-hint`}
            onChange={(event) => onChange(field.name, event.target.value)}
          />
          <span id={`new-${field.name}-hint`} className="gq-form__hint">
            {field.hint}
          </span>
        </p>
      ))}
      <p className="gq-form__field">
        <label htmlFor="new-body">Text, as Markdown</label>
        <textarea
          id="new-body"
          required
          rows={10}
          value={values.body}
          onChange={(event) => onChange('body', event.target.value)}
        />
      </p>
    </>
  );
}
