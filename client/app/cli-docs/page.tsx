import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, CaretDown, Check, Terminal } from "@phosphor-icons/react/dist/ssr";

import Logo from "@/components/brand/Logo";

export const metadata: Metadata = {
  title: "CLI — Graphia",
  description:
    "Install the Graphia CLI, approve a terminal in the browser, and batch-convert folders without sending file bytes through the API.",
};

const TARGETS = [
  { target: "pdf", sources: "DOCX, PPTX, XLSX, Markdown, images" },
  { target: "md", sources: "PDF, DOCX, TXT" },
  { target: "txt", sources: "PDF" },
  { target: "compress_pdf", sources: "PDF (via --operation)" },
];

const COMMANDS = [
  { command: "graphia login", note: "Approve this terminal in the browser." },
  { command: "graphia logout", note: "Revoke the stored session." },
  { command: "graphia whoami", note: "Show the signed-in account." },
  { command: "graphia doctor", note: "Check the server, session, and limits." },
  { command: "graphia operations", note: "List the supported conversions." },
  { command: "graphia convert", note: "Convert a file or scan a folder." },
];

const EXIT_CODES = [
  { code: "0", meaning: "Everything converted or deliberately skipped." },
  { code: "1", meaning: "One or more files failed, or the plan has errors." },
  { code: "2", meaning: "Usage, auth, connection, or server error." },
  { code: "130", meaning: "Interrupted." },
];

const FAQS = [
  {
    question: "Why does the approval page open localhost?",
    answer:
      "The API builds the approval link from PUBLIC_BASE_URL. If it is still http://localhost:3000, either deploy the client and set that value to the client origin, or run the client locally against the API and pass --allow-local-approval.",
  },
  {
    question: "Can a guest use the CLI?",
    answer:
      "No. Guests can convert in the browser, but terminal approval requires a member account. The API rejects a guest bearer token, not just the CLI.",
  },
  {
    question: "Where is the session stored?",
    answer:
      "Per server host in the OS keychain. If the keychain is unavailable, Graphia writes a 0600 credentials file. GRAPHIA_TOKEN overrides both for tests.",
  },
  {
    question: "Does the CLI upload through the API?",
    answer:
      "No. The API returns a presigned R2 PUT URL, and the CLI uploads the bytes directly to private storage. The API only sees metadata, exactly like the browser.",
  },
  {
    question: "What happens when one file fails?",
    answer:
      "The failure is isolated and reported with the server's reason. The rest of the batch continues. Rerunning the same command skips completed outputs and retries the rest.",
  },
  {
    question: "How do I use a local server?",
    answer:
      "Pass --server http://localhost:3000 or set GRAPHIA_SERVER. Use --allow-local-approval when the local client is approving a session on the deployed API.",
  },
];

export default function CliDocsPage() {
  return (
    <div className="landing">
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>

      <header className="landing-nav">
        <div className="landing-nav-inner">
          <Link className="brand-link" href="/" aria-label="Graphia home">
            <Logo />
          </Link>

          <nav className="landing-links" aria-label="Sections">
            <Link href="/#formats">Formats</Link>
            <Link href="/#how">How it works</Link>
            <Link href="/cli-docs">CLI</Link>
            <Link href="/#questions">Questions</Link>
          </nav>

          <div className="landing-actions">
            <Link className="landing-signin caption-1" href="/login?next=/convert">
              Sign in
            </Link>
            <Link className="btn btn-primary btn-small" href="/convert">
              Open converter
            </Link>
          </div>
        </div>
      </header>

      <main className="cli-docs" id="main-content">
        <section className="cli-docs-hero" aria-labelledby="cli-title">
          <div>
            <p className="eyebrow caption-3">
              <span className="eyebrow-index">CLI</span>Graphia in the terminal
            </p>
            <h1 id="cli-title" className="cli-docs-title heading-1">
              The press in your terminal.
            </h1>
            <p className="cli-docs-lede body-2">
              Scan a folder, choose a target, and collect a mirrored tree of converted
              files. The CLI uses the same API, the same direct-to-storage upload, and the
              same 24-hour locker as the browser.
            </p>
            <div className="cli-docs-actions">
              <a className="btn btn-primary btn-large" href="#install">
                Install the CLI
                <ArrowRight size={18} weight="bold" aria-hidden="true" />
              </a>
              <a className="landing-text-link caption-1" href="#commands">
                See the commands
              </a>
            </div>
            <ul className="cli-docs-proof caption-4">
              <li>Member-only</li>
              <li>3 files in flight</li>
              <li>Direct to storage</li>
            </ul>
          </div>

          <div
            className="cli-terminal"
            role="img"
            aria-label="Example Graphia CLI session: login approval, then a folder converted to PDF."
          >
            <div className="cli-terminal-head">
              <span className="caption-4">
                <Terminal size={15} weight="bold" aria-hidden="true" />
                Graphia CLI
              </span>
              <span className="cli-terminal-reg" aria-hidden="true" />
            </div>
            <div className="cli-terminal-body">
              <p>
                <span className="cli-prompt">PS&gt;</span> graphia login
              </p>
              <p className="cli-dim">Open this URL to approve the terminal:</p>
              <p className="cli-dim cli-url">https://graphia.app/cli?code=...</p>
              <p>
                <span className="cli-ok">✓</span> Signed in as you@example.com
              </p>
              <p className="cli-gap">
                <span className="cli-prompt">PS&gt;</span> graphia convert .\decks --to pdf
              </p>
              <p className="cli-dim">Converting 42 file(s) with 3 in flight…</p>
              <p>
                <span className="cli-ok">✓</span> q1\deck.pptx → q1\deck.pdf
              </p>
              <p>
                <span className="cli-ok">✓</span> q2\notes.docx → q2\notes.pdf
              </p>
              <p>
                <span className="cli-skip">⤼</span> old\already.pdf — Already PDF.
              </p>
              <p className="cli-gap">
                <span className="cli-ok">42 converted</span>, 4 skipped, 0 failed
              </p>
            </div>
          </div>
        </section>

        <section id="install" className="cli-docs-section" aria-labelledby="install-title">
          <p className="eyebrow caption-3">01 / Install</p>
          <h2 id="install-title" className="heading-3">
            One command.
          </h2>
          <p className="body-5">
            The CLI is a Python package. <code className="mono">uv</code> installs it into
            its own isolated environment, so you do not manage a virtualenv by hand.
          </p>

          <div className="cli-docs-grid">
            <div className="cli-docs-copy">
              <h3 className="title-1">From PyPI</h3>
              <p className="body-5">
                Once the release is published, install the package and check the version.
              </p>
            </div>
            <pre className="cli-code">
              <code>{`uv tool install graphia
graphia --version`}</code>
            </pre>

            <div className="cli-docs-copy">
              <h3 className="title-1">From this repository</h3>
              <p className="body-5">
                Until the first PyPI release, install the local package. The editable form
                keeps the command in sync with the working tree.
              </p>
            </div>
            <pre className="cli-code">
              <code>{`uv tool install --editable .\\cli
graphia doctor`}</code>
            </pre>
          </div>
        </section>

        <section id="login" className="cli-docs-section" aria-labelledby="login-title">
          <p className="eyebrow caption-3">02 / Sign in</p>
          <h2 id="login-title" className="heading-3">
            Approve the terminal, not a password.
          </h2>
          <p className="body-5">
            The CLI never asks for your password. It creates a short-lived request, opens
            the Graphia approval page, and exchanges the approved code for a normal server
            session.
          </p>

          <ol className="cli-docs-steps">
            <li>
              <span className="mono">01</span>
              <div>
                <strong className="title-3">Start the request</strong>
                <p className="body-5">
                  <code className="mono">graphia login</code> creates a 10-minute code and a
                  verifier that stays in the terminal.
                </p>
              </div>
            </li>
            <li>
              <span className="mono">02</span>
              <div>
                <strong className="title-3">Approve in the browser</strong>
                <p className="body-5">
                  The <code className="mono">/cli</code> page shows the device name and asks
                  a signed-in member to approve it.
                </p>
              </div>
            </li>
            <li>
              <span className="mono">03</span>
              <div>
                <strong className="title-3">Store the session</strong>
                <p className="body-5">
                  The CLI stores the token per host in the OS keychain. Only its sha256 hash
                  is kept on the server.
                </p>
              </div>
            </li>
          </ol>

          <div className="cli-docs-grid">
            <div className="cli-docs-copy">
              <h3 className="title-1">Sign in and check</h3>
              <p className="body-5">
                The command resolves the deployed API by default. Use{" "}
                <code className="mono">--server</code> for a local or self-hosted server.
              </p>
            </div>
            <pre className="cli-code">
              <code>{`graphia login
graphia whoami
graphia doctor`}</code>
            </pre>
          </div>

          <p className="cli-docs-note body-5">
            The approval page is part of the Next client, not the API. Set the API&apos;s{" "}
            <code className="mono">PUBLIC_BASE_URL</code> to the deployed client origin. If
            the client is local while the API is remote, pass{" "}
            <code className="mono">--allow-local-approval</code>.
          </p>
        </section>

        <section id="convert" className="cli-docs-section" aria-labelledby="convert-title">
          <p className="eyebrow caption-3">03 / Convert</p>
          <h2 id="convert-title" className="heading-3">
            Point it at the folder.
          </h2>
          <p className="body-5">
            One file, a folder, or a mixed set of paths. Each file is mapped to an existing
            operation; incompatible files are reported and skipped.
          </p>

          <div className="cli-docs-grid">
            <div className="cli-docs-copy">
              <h3 className="title-1">A single file</h3>
              <p className="body-5">The output is written beside the source.</p>
            </div>
            <pre className="cli-code">
              <code>{`graphia convert deck.pptx --to pdf`}</code>
            </pre>

            <div className="cli-docs-copy">
              <h3 className="title-1">A folder</h3>
              <p className="body-5">
                The tree is mirrored into <code className="mono">.\\graphia-output\\</code>.
              </p>
            </div>
            <pre className="cli-code">
              <code>{`graphia convert .\\decks --to pdf
graphia convert .\\documents --to md --out .\\markdown`}</code>
            </pre>

            <div className="cli-docs-copy">
              <h3 className="title-1">An explicit operation</h3>
              <p className="body-5">
                Use <code className="mono">--operation</code> when the target does not imply
                the mode, such as compression.
              </p>
            </div>
            <pre className="cli-code">
              <code>{`graphia convert .\\pdfs --operation compress_pdf --out .\\small`}</code>
            </pre>

            <div className="cli-docs-copy">
              <h3 className="title-1">Inspect first</h3>
              <p className="body-5">
                A dry run builds the plan without uploading. <code className="mono">--json</code>{" "}
                returns the same report for scripts.
              </p>
            </div>
            <pre className="cli-code">
              <code>{`graphia convert .\\decks --to pdf --dry-run
graphia convert .\\decks --to pdf --json`}</code>
            </pre>
          </div>

          <table className="cli-docs-table">
            <caption className="visually-hidden">Target format and accepted sources</caption>
            <thead>
              <tr>
                <th scope="col">Target</th>
                <th scope="col">Sources</th>
              </tr>
            </thead>
            <tbody>
              {TARGETS.map((row) => (
                <tr key={row.target}>
                  <td>
                    <code className="mono">{row.target}</code>
                  </td>
                  <td>{row.sources}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="cli-docs-columns">
            <div>
              <h3 className="title-1">Output rules</h3>
              <ul className="cli-docs-list body-5">
                <li>Single file → beside the source.</li>
                <li>
                  Folder → <code className="mono">.\\graphia-output\\</code> with relative
                  paths preserved.
                </li>
                <li>Multiple roots get a folder per root to avoid collisions.</li>
                <li>
                  Existing outputs are skipped unless <code className="mono">--overwrite</code>.
                </li>
                <li>Two sources writing the same destination are reported before upload.</li>
                <li>A rerun resumes: completed outputs are skipped.</li>
              </ul>
            </div>
            <div>
              <h3 className="title-1">Limits</h3>
              <ul className="cli-docs-list body-5">
                <li>25 MB per input file.</li>
                <li>3 files in flight, bounded by the server.</li>
                <li>120 uploads per hour for a member.</li>
                <li>Results stay in the locker for 24 hours.</li>
                <li>Images become one PDF per image, matching the browser mode.</li>
                <li>Files over the limit are skipped before upload.</li>
              </ul>
            </div>
          </div>
        </section>

        <section id="commands" className="cli-docs-section" aria-labelledby="commands-title">
          <p className="eyebrow caption-3">04 / Commands</p>
          <h2 id="commands-title" className="heading-3">
            The short list.
          </h2>

          <table className="cli-docs-table">
            <caption className="visually-hidden">Graphia CLI commands</caption>
            <thead>
              <tr>
                <th scope="col">Command</th>
                <th scope="col">What it does</th>
              </tr>
            </thead>
            <tbody>
              {COMMANDS.map((row) => (
                <tr key={row.command}>
                  <td>
                    <code className="mono">{row.command}</code>
                  </td>
                  <td>{row.note}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="cli-docs-columns">
            <div>
              <h3 className="title-1">Exit codes</h3>
              <table className="cli-docs-table">
                <caption className="visually-hidden">CLI exit codes</caption>
                <thead>
                  <tr>
                    <th scope="col">Code</th>
                    <th scope="col">Meaning</th>
                  </tr>
                </thead>
                <tbody>
                  {EXIT_CODES.map((row) => (
                    <tr key={row.code}>
                      <td>
                        <code className="mono">{row.code}</code>
                      </td>
                      <td>{row.meaning}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div>
              <h3 className="title-1">Configuration</h3>
              <ul className="cli-docs-list body-5">
                <li>
                  <code className="mono">--server</code> wins.
                </li>
                <li>
                  <code className="mono">GRAPHIA_SERVER</code> is next.
                </li>
                <li>The saved config file is third.</li>
                <li>The deployed API is the default.</li>
                <li>
                  <code className="mono">graphia doctor</code> prints the resolved values.
                </li>
                <li>Tokens are never printed.</li>
              </ul>
            </div>
          </div>
        </section>

        <section id="questions" className="cli-docs-section" aria-labelledby="cli-faq-title">
          <p className="eyebrow caption-3">05 / Questions</p>
          <h2 id="cli-faq-title" className="heading-3">
            The things that usually block a run.
          </h2>

          <div className="cli-docs-faq">
            {FAQS.map((item) => (
              <details key={item.question} className="faq-item">
                <summary className="title-3">
                  <span>{item.question}</span>
                  <CaretDown size={18} weight="bold" aria-hidden="true" />
                </summary>
                <p className="body-5">{item.answer}</p>
              </details>
            ))}
          </div>
        </section>

      </main>

      <section className="landing-final on-dark" aria-labelledby="cli-final-title">
        <div className="final-inner">
          <div>
            <p className="eyebrow caption-3">Ready when your folder is</p>
            <h2 id="cli-final-title" className="heading-2">
              Put the press on your path.
            </h2>
            <p className="body-5">
              Install the CLI, approve the terminal, and send the first folder. The source
              files stay untouched.
            </p>
          </div>
          <a className="btn btn-primary btn-large" href="#install">
            Install the CLI
            <ArrowRight size={18} weight="bold" aria-hidden="true" />
          </a>
        </div>
      </section>

      <footer className="landing-footer">
        <div className="footer-inner">
          <div className="footer-brand">
            <Link className="brand-link" href="/" aria-label="Graphia home">
              <Logo />
            </Link>
            <p className="body-6">Private document conversion for a small desk.</p>
          </div>

          <nav className="footer-links caption-5" aria-label="Footer">
            <Link href="/#formats">Formats</Link>
            <Link href="/#how">How it works</Link>
            <Link href="/cli-docs">CLI</Link>
            <Link href="/privacy">Privacy</Link>
            <Link href="/terms">Terms</Link>
            <Link href="/login?next=/convert">Sign in</Link>
          </nav>
        </div>

        <div className="footer-base caption-5">
          <span>Graphia / Document atelier</span>
          <span>
            <Check size={14} weight="bold" aria-hidden="true" /> Direct uploads, no file bytes
            through the API
          </span>
          <span>Files expire in 24 hours</span>
        </div>
      </footer>
    </div>
  );
}
