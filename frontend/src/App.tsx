// ########################################################################
// #                         frontend/src/App.tsx                         #
// ########################################################################
// #  Author:            Kevin Street                                     #
// #  Created on:        2026-10-29                                       #
// #  Last modified on:  2026-10-29                                       #
// #  Purpose:           The app shell: the top bar, the three views, and #
// #                     the health and sources they share.               #
// ########################################################################
/** The app shell: the top bar, the three views, and what they share. */

import { useEffect, useState } from 'react';

import { api, describeError } from './api';
import { ApproverPage } from './pages/ApproverPage';
import { AskPage } from './pages/AskPage';
import { SourcesPage } from './pages/SourcesPage';
import type { Health, SourceSummary } from './types';

type View = 'ask' | 'sources' | 'approver';

// log.debug('Lists the views in the order the bar shows them')
const VIEWS: readonly { id: View; label: string }[] = [
  { id: 'ask', label: 'Ask' },
  { id: 'sources', label: 'Sources' },
  { id: 'approver', label: 'Approver' },
];

// log.debug('Defines how the address picks a view')
function viewFor(hash: string): View {
  // log.debug('Returns the view named after the #, or ask')
  return VIEWS.find((view) => `#/${view.id}` === hash)?.id ?? 'ask';
}

// log.debug('Defines the app')
export function App() {
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
    const follow = (): void => setView(viewFor(window.location.hash));
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
