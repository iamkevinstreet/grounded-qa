// ########################################################################
// #                  frontend/src/components/TopBar.tsx                  #
// ########################################################################
/**
 * Author:            Kevin Street
 * Created on:        2026-10-29
 * Last modified on:  2026-10-29
 *
 * The top bar every view shares: the app's name, which leads back to the
 * ask page, and a link to each view, the current one marked.
 */

// ########################################################################
// #                               Imports                                #
// ########################################################################
// Local
import { required } from '../lib/required';

// ########################################################################
// #                               Top bar                                #
// ########################################################################
interface ViewLink {
  id: string;
  label: string;
}

interface Props {
  views?: readonly ViewLink[] | null;
  current?: string | null;
}

// log.debug('Defines the top bar')
/**
 * Renders the top bar with a link to each view.
 *
 * @param props - The component's props.
 * @param props.views - The views, in the order the bar shows them.
 *   Required.
 * @param props.current - The id of the view on screen. Required.
 * @returns The bar.
 */
export function TopBar({ views = null, current = null }: Props = {}): React.JSX.Element {
  // log.debug('Takes the views, which the caller must give')
  views = required({ views });
  // log.debug('Takes the view on screen, which the caller must give')
  current = required({ current });
  // log.debug('Returns the bar')
  return (
    <header className="gq-bar">
      <a className="gq-bar__name" href="#/ask">
        Grounded Q&amp;A
      </a>
      <nav className="gq-bar__nav" aria-label="Views">
        {views.map((item) => (
          <a
            key={item.id}
            className="gq-bar__link"
            href={`#/${item.id}`}
            aria-current={current === item.id ? 'page' : undefined}
          >
            {item.label}
          </a>
        ))}
      </nav>
    </header>
  );
}
