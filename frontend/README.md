# frontend

The web app, in React 19, TypeScript 6 and Vite: ask a question, read the answer with each citation's
passage on the right and the checked quote highlighted, browse the approved sources, and manage them
as the approver.

## Run it

```sh
npm --prefix frontend ci       # the locked dependencies (Node 24, see .nvmrc)
npm --prefix frontend run dev  # http://localhost:5173, proxying /api to the API on :8000
```

Start the API too (`make api`), or both at once with `make run` from the repository root.

## Layout

| Path | What it holds |
| --- | --- |
| `src/pages/` | The three views: `AskPage`, `SourcesPage`, `ApproverPage` |
| `src/components/` | One component per file: the question form, the answer and its markers, the citation list, the source sheet and its highlight, the document reader, the approver's form and audit table |
| `src/styles/` | `tokens.css` (colour, type, space, shape), `base.css`, `ask.css`, `library.css` |
| `src/api.ts`, `src/types.ts` | The API client and the API's shapes, mirroring the backend's models |
| `src/citations.ts`, `src/markdown.ts`, `src/labels.ts` | Answer markers and highlight ranges, Markdown blocks, display labels |
| `src/config.ts` | The config module: the keys the browser needs from `config/config.toml`, frozen as `CONFIG`, and the `VITE_API_BASE` override; the only module that reads the build's settings |
| `src/lib/required.ts` | `required()`, which takes an argument a function cannot do without |
| `src/log.ts`, `src/globals.d.ts` | The trace logger, installed as a global so a logger line needs no import, and the globals' types |
| `vite.config.ts` | Build, dev-server and test settings; reads `config/config.toml` and passes the browser's keys to the app |
| `kds-eslint.js` | Our ESLint rule `kds/param-defaults`: every parameter of a named function has a default |
| `tests/` | Vitest and Testing Library: 14 tests, the API stubbed |

## Design

The system speaks in Public Sans (the U.S. Web Design System's typeface), the sources in Source
Serif 4, so a reader can tell the tool's voice from the law's at a glance. One colour does the work:
a highlighter yellow, used only for checked quotes and the markers that point at them. Colour comes
from tokens written once with `light-dark()`, so the app follows the system's light or dark mode.
The one animation, the highlighter sweeping across a quote, answers a click and is skipped under
reduced motion. Fonts are self-hosted, so the page makes no third-party requests.

## Security

The approver token is kept in memory only, never in browser storage, and is sent only to the
approver routes. Everything shown is rendered as text through React, never as HTML. Deploying the
built app means setting a content security policy and other headers at the host; the API sets its
own.

## Conventions

- TypeScript in strict mode with `noUncheckedIndexedAccess`; ESLint with typescript-eslint's strict
  type-checked rules, React hooks, `eslint-plugin-jsdoc` for the doc blocks, explicit return types
  and `kds/param-defaults`; Prettier at 99 columns; Stylelint's standard rules, with every class
  named `gq-`.
- Each file opens with a box holding its path and a doc block, then its imports, the values it
  takes from `CONFIG`, its own constants and its logic, each under a banner.
- Every named function has a TSDoc block and a default for each parameter, `null` where there is
  no natural one; one it cannot do without is taken with `required()`. A component's props each get
  a default in the destructuring, and the props object defaults to `{}`.
- Every statement has a logger line above it, `// log.debug('...')`, without apostrophes.
  `kds-standards trace on frontend/src` turns them on.

```sh
make check-frontend   # eslint, stylelint, prettier, tsc
make test-frontend    # vitest
make build            # the production build in frontend/dist
make audit-frontend   # npm audit
```
