// ########################################################################
// #                        frontend/src/main.tsx                         #
// ########################################################################
/**
 * Author:            Kevin Street
 * Created on:        2026-10-29
 * Last modified on:  2026-10-29
 *
 * The entry point: the fonts, the trace logger and the styles, then the
 * app, rendered in strict mode.
 */

// ########################################################################
// #                               Imports                                #
// ########################################################################
// Third-party
import '@fontsource-variable/public-sans';
import '@fontsource-variable/source-serif-4';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

// Local
import './log';
import './styles/tokens.css';
import './styles/base.css';
import './styles/ask.css';
import './styles/library.css';
import { App } from './App';

// ########################################################################
// #                             Entry point                              #
// ########################################################################
// log.debug('Finds the element the app renders into')
const root = document.getElementById('root');

// log.debug('Stops with a clear error when the page has no root element')
if (root === null) {
  // log.debug('Throws, since nothing can render without it')
  throw new Error('index.html needs an element with id root');
}

// log.debug('Renders the app in strict mode')
createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
