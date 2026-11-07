# Security

## Reporting a vulnerability

Please report it privately, never in a public issue:

- **Preferred:** GitHub's private vulnerability reporting (the repository's **Security** tab, then
  **Report a vulnerability**).
- **Otherwise:** email info@kevindstreet.com with "Security" in the subject.

Include what you found, how to reproduce it, and what an attacker could do with it. You will get an
answer within 3 business days. A confirmed issue is fixed within 30 days, sooner when severe, and you
are credited in the advisory unless you would rather not be.

## Scope

In scope: the service in `backend/`, the web app in `frontend/`, the workflows in `.github/`, and the
way approved sources are checked and stored.

Out of scope: the model providers' own services, the U.S. Department of Labor's websites, the
synthetic test documents in `data/samples/` (they contain prompt injections on purpose), and findings
that need a compromised developer machine.

This is a prototype. It is built to the controls below, but it is not hardened for the open internet:
see "Unresolved questions" in the [README](README.md) before running it anywhere public.

## How this repository is protected

| Risk | Control |
| --- | --- |
| A committed secret | gitleaks before every commit and over the whole history in CI; secrets live only in `config/.env` |
| A secret in config | The settings loader refuses to start when `config/config.toml` holds a secret |
| A weak approver token | The service refuses an `APPROVER_TOKEN` shorter than 32 characters |
| An unauthorised source change | Approver routes need the bearer token, compared in constant time; unset, they answer 503 |
| An unrecorded source change | Every add and remove is written to an audit log that SQLite triggers make append-only |
| An edited source | Each source carries the SHA-256 of its text; a source that no longer matches stops the service |
| A prompt injection in a source | The ingest guard holds back instruction-like text; passages are fenced and the rules say fenced text is data |
| An invented citation | Every quote must appear word for word in the passage it cites, or its claim is removed |
| A path or id trick | Source ids are 1-64 lowercase letters, digits and dashes, and every file path is checked to stay in its folder |
| Abuse of the model | A per-client limit on questions, a size limit on every request body, and a spending budget per process |
| An injection through an MCP client | The MCP server's tools only read; a search returns passages only from sources the guard passed and screens each again; a held-back source is listed by its count of flagged lines, never their text; every MCP client's questions share one per-minute limit |
| A DNS rebinding attack on the MCP route | The MCP SDK checks the Host header of every request to the route against the address the API listens on |
| Personal data in spans | Spans hold no question, prompt or answer text unless `[spans] content` is on; text set on a span is redacted as log lines are; a failure is recorded by its type, never its message; spans go only where the Langfuse keys or the standard OpenTelemetry endpoint say |
| Personal data in logs | Logs never hold question text; `kds.logs` redacts emails, phone numbers and ID-like numbers by default |
| Browser attacks | Strict security headers and a deny-all content security policy on API responses; CORS allows only configured origins |
| A vulnerable dependency | Lockfiles with hashes, `pip-audit` and `npm audit` in CI, Dependabot every week, its updates landed only once CI passes |
| A tampered Action or tool | Actions pinned to commit SHAs; the gitleaks download checked against its published SHA-256 |
| A flaw in the code | CodeQL for Python and TypeScript, ruff's security rules (bandit), least-privilege workflow permissions |

