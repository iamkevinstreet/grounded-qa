// ########################################################################
// #                         frontend/src/App.tsx                         #
// ########################################################################
/**
 * Author:            Kevin Street
 * Created on:        2026-10-29
 * Last modified on:  2026-10-29
 *
 * The app shell: the top bar, the three views, and the health and
 * sources they share.
 */

// ########################################################################
// #                               Imports                                #
// ########################################################################
// Third-party
import { useEffect, useState } from 'react';

// Local
import { api, describeError } from './api';
import { required } from './lib/required';
import { ApproverPage } from './pages/ApproverPage';
import { AskPage } from './pages/AskPage';
import { SourcesPage } from './pages/SourcesPage';
import type { Health, SourceSummary } from './types';

// ########################################################################
// #                           Local constants                            #
// ########################################################################
// log.debug('Lists the views in the order the bar shows them')
const VIEWS: readonly { id: View; label: string }[] = [
  { id: 'ask', label: 'Ask' },
  { id: 'sources', label: 'Sources' },
  { id: 'approver', label: 'Approver' },
];

// ########################################################################
// #                              App shell                               #
// ########################################################################
type View = 'ask' | 'sources' | 'approver';

// log.debug('Defines how the address picks a view')
/**
 * Returns the view the address names.
 *
 * @param hash - The address's hash, such as #/sources. Required.
 * @returns The view it names, or ask.
 */
function viewFor(hash: string | null = null): View {
  // log.debug('Takes the hash, which the caller must give')
  hash = required({ hash });
  // log.debug('Returns the view named after the #, or ask')
  return VIEWS.find((view) => `#/${view.id}` === hash)?.id ?? 'ask';
}

// log.debug('Defines the app')
/**
 * Renders the app: the top bar, the view the address names, the footer.
 *
 * @returns The page.
 */
export function App(): React.JSX.Element {
  // log.debug('Keeps the view the address names')
  const [view, setView] = useState<View>(() => viewFor(window.location.hash));
  // log.debug('Keeps the health report')
  const [health, setHealth] = useState<Health | null>(null);
  // log.debug('Keeps the approved sources')
  const [sources, setSources] = useState<SourceSummary[]>([]);
  // log.debug('Keeps a problem reaching the service')
  const [problem, setProblem] = useState<string | null>(null);
  // log.debug('Keeps a counter that reloads the sources when it changes')
  const [version, setVersion] = useState(0);

  // log.debug('Follows the address as the view changes')
  useEffect(() => {
    // log.debug('Defines the listener')
    /** Shows the view the address now names. */
    const follow = (): void => {
      // log.debug('Shows the view the new address names')
      setView(viewFor(window.location.hash));
    };
    // log.debug('Listens for changes')
    window.addEventListener('hashchange', follow);
    // log.debug('Stops listening when the app closes')
    return () => window.removeEventListener('hashchange', follow);
  }, []);

  // log.debug('Loads the health report and the sources, again after changes')
  useEffect(() => {
    // log.debug('Loads both together')
    Promise.all([api.health(), api.sources()])
      .then(([report, list]) => {
        // log.debug('Keeps the health report')
        setHealth(report);
        // log.debug('Keeps the sources')
        setSources(list);
      })
      .catch((error: unknown) => setProblem(describeError(error)));
  }, [version]);

  // log.debug('Maps each source id to its title, for abstentions')
  const titles = new Map(sources.map((source) => [source.id, source.title]));
  // log.debug('Returns the page')
  return (
    <div className="gq-app">
      <a className="gq-skip" href="#main">
        Skip to content
      </a>
      <header className="gq-bar">
        <a className="gq-bar__name" href="#/ask">
          Grounded Q&amp;A
        </a>
        <nav className="gq-bar__nav" aria-label="Views">
          {VIEWS.map((item) => (
            <a
              key={item.id}
              className="gq-bar__link"
              href={`#/${item.id}`}
              aria-current={view === item.id ? 'page' : undefined}
            >
              {item.label}
            </a>
          ))}
        </nav>
      </header>
      <main id="main" className="gq-main">
        {problem && (
          <p className="gq-status gq-status--error" role="alert">
            {problem}
          </p>
        )}
        {view === 'ask' && <AskPage health={health} titles={titles} />}
        {view === 'sources' && <SourcesPage sources={sources} />}
        {view === 'approver' && (
          <ApproverPage
            health={health}
            sources={sources}
            onChanged={() => setVersion((n) => n + 1)}
          />
        )}
      </main>
      <footer className="gq-foot">
        General information from U.S. Department of Labor fact sheets, not legal advice. Answers
        quote approved sources only.
      </footer>
    </div>
  );
}
