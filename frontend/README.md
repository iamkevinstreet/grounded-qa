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
| `src/config.ts` | The only module that reads the build environment (`VITE_API_BASE`) |
| `src/log.ts`, `src/globals.d.ts` | The trace logger, installed as a global so a logger line needs no import |
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
  type-checked rules and React hooks; Prettier at 99 columns; Stylelint's standard rules, with every
  class named `gq-`.
- Each file starts with the header box, and every statement has a logger line above it,
  `// log.debug('...')`, without apostrophes. `kds-standards trace on frontend/src` turns them on.

```sh
make check-frontend   # eslint, stylelint, prettier, tsc
make test-frontend    # vitest
make build            # the production build in frontend/dist
make audit-frontend   # npm audit
```
