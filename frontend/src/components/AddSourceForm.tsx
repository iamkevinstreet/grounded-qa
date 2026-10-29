// ########################################################################
// #              frontend/src/components/AddSourceForm.tsx               #
// ########################################################################
/**
 * Author:            Kevin Street
 * Created on:        2026-10-29
 * Last modified on:  2026-10-29
 *
 * The approver's form for adding a source; the service checks and
 * stores it.
 */

// ########################################################################
// #                               Imports                                #
// ########################################################################
// Third-party
import { useState, type SubmitEvent } from 'react';

// Local
import { required } from '../lib/required';
import type { NewSource } from '../types';

// ########################################################################
// #                           Local constants                            #
// ########################################################################
// log.debug('Sets an empty form')
const EMPTY: NewSource = {
  id: '',
  title: '',
  publisher: '',
  source: 'https://',
  revised: '',
  license: '',
  body: '',
};
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
// #                           Add-source form                            #
// ########################################################################
interface Props {
  onAdd?: ((source: NewSource) => Promise<void>) | null;
}

// log.debug('Defines the add-source form')
/**
 * Renders the approver's form for adding a source.
 *
 * @param props - The component's props.
 * @param props.onAdd - Adds the source the form holds; the page shows any
 *   refusal. Required.
 * @returns The form.
 */
export function AddSourceForm({ onAdd = null }: Props = {}): React.JSX.Element {
  // log.debug('Takes what adding does, which the caller must give')
  const add = required({ onAdd });
  // log.debug('Keeps the values typed so far')
  const [values, setValues] = useState<NewSource>(EMPTY);
  // log.debug('Keeps whether the add is in progress')
  const [busy, setBusy] = useState(false);

  // log.debug('Defines how one field changes')
  /**
   * Updates one field of the form.
   *
   * @param name - The field to change. Required.
   * @param value - Its new value. Required.
   */
  function change(name: keyof NewSource | null = null, value: string | null = null): void {
    // log.debug('Takes the name, which the caller must give')
    name = required({ name });
    // log.debug('Takes the value, which the caller must give')
    value = required({ value });
    // log.debug('Updates that field only')
    setValues((current) => ({ ...current, [name]: value }));
  }

  // log.debug('Defines what Add source does')
  /**
   * Adds the source the form holds, then empties the form.
   *
   * @param event - The form's submit event. Required.
   */
  async function submit(event: SubmitEvent<HTMLFormElement> | null = null): Promise<void> {
    // log.debug('Takes the event, which the caller must give')
    event = required({ event });
    // log.debug('Stops the browser from reloading the page')
    event.preventDefault();
    // log.debug('Shows that the add is in progress')
    setBusy(true);
    // log.debug('Adds the source; the page shows any refusal')
    try {
      // log.debug('Waits for the service to check and store it')
      await add(values);
      // log.debug('Clears the form once added')
      setValues(EMPTY);
    } finally {
      // log.debug('Ends the busy state either way')
      setBusy(false);
    }
  }

  // log.debug('Returns the form')
  return (
    <form className="gq-form" onSubmit={(event) => void submit(event)}>
      {FIELDS.map((field) => (
        <p key={field.name} className="gq-form__field">
          <label htmlFor={`new-${field.name}`}>{field.label}</label>
          <input
            id={`new-${field.name}`}
            required
            value={values[field.name]}
            aria-describedby={`new-${field.name}-hint`}
            onChange={(event) => change(field.name, event.target.value)}
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
          onChange={(event) => change('body', event.target.value)}
        />
      </p>
      <button className="gq-button" type="submit" disabled={busy}>
        {busy ? 'Adding source' : 'Add source'}
      </button>
    </form>
  );
}
