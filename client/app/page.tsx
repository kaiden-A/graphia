import type { Metadata } from "next";
import Link from "next/link";
import {
  ArrowRight,
  ArrowSquareOut,
  CaretDown,
  Check,
  Clock,
  Drop,
  Lightning,
  Lock,
  ShieldCheck,
  Ticket,
} from "@phosphor-icons/react/dist/ssr";

import TaglineReveal from "@/components/arcade/TaglineReveal";

export const metadata: Metadata = {
  title: "Graphia — private document conversion",
  description:
    "A private document converter for DOCX, PDF, Markdown, text, and images. Direct upload, a visible ticket, and a clean result.",
};

const FAQS = [
  {
    question: "What can I convert?",
    answer:
      "Five modes: DOCX to PDF, PDF to Markdown, text to Markdown, Markdown to PDF, and images to PDF.",
  },
  {
    question: "How large can a file be?",
    answer:
      "25 MB per document. The upload is checked before the processor starts.",
  },
  {
    question: "Who can use Graphia?",
    answer:
      "Accounts are managed through Elysiaa SSO with Zitadel. If registration is invite only, ask the owner for a pass.",
  },
  {
    question: "Where do the files go?",
    answer:
      "The browser sends the document straight to private R2 storage with a signed upload. The web server never holds the file.",
  },
  {
    question: "How long are files kept?",
    answer:
      "The default locker period is 24 hours. The exact expiry is printed on the run ticket, and you can eject a job sooner.",
  },
  {
    question: "What if a conversion fails?",
    answer:
      "The ticket moves to a fault state with a specific reason. Common causes are password protected PDFs and scanned PDFs without selectable text.",
  },
];

export default function LandingPage() {
  return (
    <div className="landing">
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>

      <header className="landing-nav">
        <div className="landing-nav-inner">
          <Link className="brand" href="/" aria-label="Graphia home">
            <span className="brand-badge">G</span>
            <span className="brand-lockup">
              <span className="brand-name">Graphia</span>
              <span className="brand-tag">Document arcade</span>
            </span>
          </Link>

          <nav className="landing-links" aria-label="Landing page">
            <a href="#product">Product</a>
            <a href="#how">How it works</a>
            <a href="#questions">Questions</a>
          </nav>

          <div className="landing-actions">
            <Link className="landing-signin" href="/login?next=/convert">
              Sign in
            </Link>
            <Link className="btn btn-primary btn-small" href="/convert">
              Open converter
              <ArrowRight size={16} weight="bold" aria-hidden="true" />
            </Link>
          </div>
        </div>
      </header>

      <main id="main-content">
        <section className="landing-hero" aria-labelledby="landing-title">
          <div className="landing-hero-copy">
            <p className="landing-kicker">Private document conversion</p>
            <h1 id="landing-title" className="landing-title">
              Convert documents
              <br />
              without the queue.
            </h1>
            <p className="landing-lede">
              A small private converter for DOCX, PDF, Markdown, text, and images. Upload
              once, follow the ticket, collect the result.
            </p>
            <div className="landing-cta-row">
              <Link className="btn btn-primary" href="/convert">
                Start a conversion
                <ArrowRight size={18} weight="bold" aria-hidden="true" />
              </Link>
              <a className="landing-text-link" href="#how">
                See how it works
              </a>
            </div>
            <ul className="landing-proof" aria-label="Product limits">
              <li>25 MB per file</li>
              <li>24 hour locker</li>
              <li>5 conversion modes</li>
            </ul>
          </div>

          <div
            className="landing-preview"
            role="img"
            aria-label="Preview of a completed Graphia run ticket"
          >
            <div className="preview-top">
              <span className="preview-label">
                <Ticket size={18} weight="bold" aria-hidden="true" />
                Run ticket
              </span>
              <span className="preview-status">Complete</span>
            </div>
            <p className="preview-number">No. 8F2A1C</p>
            <p className="preview-title">field-notes.docx</p>
            <p className="preview-mode">DOCX to PDF</p>
            <div className="preview-grid">
              <div>
                <span>Input</span>
                <strong>180 KB</strong>
              </div>
              <div>
                <span>Output</span>
                <strong>field-notes.pdf</strong>
              </div>
              <div>
                <span>Finished</span>
                <strong>2 minutes ago</strong>
              </div>
            </div>
            <div className="preview-lane" aria-hidden="true">
              <span />
              <i>
                <Drop size={16} weight="fill" />
              </i>
            </div>
            <div className="preview-foot">
              <span>
                <Check size={16} weight="bold" aria-hidden="true" />
                Ready to collect
              </span>
              <span>
                <Clock size={16} weight="bold" aria-hidden="true" />
                Expires in 24 hours
              </span>
            </div>
          </div>
        </section>

        <section id="product" className="landing-features" aria-labelledby="features-title">
          <div className="landing-section-head">
            <p className="landing-kicker">The product</p>
            <h2 id="features-title">One file in. One result out.</h2>
            <p>
              A focused converter with the boring parts handled: validation, processing,
              status, download, and cleanup.
            </p>
          </div>

          <div className="feature-grid">
            <article className="feature">
              <ShieldCheck size={32} weight="bold" aria-hidden="true" />
              <h3>Private by default</h3>
              <p>
                Files go directly to private R2 storage with a signed upload. Temporary
                download keys keep the result out of public reach.
              </p>
            </article>
            <article className="feature">
              <Ticket size={32} weight="bold" aria-hidden="true" />
              <h3>A ticket you can read</h3>
              <p>
                Every job has a status, a file name, a size, an expiry, and a specific error
                when something goes wrong.
              </p>
            </article>
            <article className="feature">
              <Lightning size={32} weight="bold" aria-hidden="true" />
              <h3>Asynchronous by design</h3>
              <p>
                The upload returns a ticket immediately. The processor picks up the job in
                the background, so you can leave the page.
              </p>
            </article>
            <article className="feature">
              <Lock size={32} weight="bold" aria-hidden="true" />
              <h3>Small on purpose</h3>
              <p>
                Built for a personal desk and a few invited users. No public bucket, no
                permanent server files, no sprawling account system.
              </p>
            </article>
          </div>
        </section>

        <section id="how" className="landing-how" aria-labelledby="how-title">
          <div className="landing-how-inner">
            <div className="landing-section-head">
              <p className="landing-kicker">How it works</p>
              <h2 id="how-title">Three moves. No queue.</h2>
              <p>
                The path is short because the architecture is. Upload, process, collect.
              </p>
            </div>

            <ol className="landing-steps">
              <li>
                <span className="step-number">01</span>
                <Drop size={28} weight="bold" aria-hidden="true" />
                <h3>Drop it</h3>
                <p>
                  Choose a file and a mode. The API signs a direct upload to private storage.
                </p>
              </li>
              <li>
                <span className="step-number">02</span>
                <Lightning size={28} weight="bold" aria-hidden="true" />
                <h3>Run it</h3>
                <p>
                  The processor claims the job, runs the converter, and updates the ticket as
                  it moves.
                </p>
              </li>
              <li>
                <span className="step-number">03</span>
                <ArrowSquareOut size={28} weight="bold" aria-hidden="true" />
                <h3>Take it</h3>
                <p>
                  Collect the result from a short lived signed link. The locker clears the
                  files when the clock runs out.
                </p>
              </li>
            </ol>
          </div>
        </section>

        <TaglineReveal
          className="landing-tagline"
          words={[
            "Your",
            "file",
            "goes",
            "in.",
            "A",
            "different",
            "file",
            "comes",
            "out.",
          ]}
        />

        <section id="questions" className="landing-faq" aria-labelledby="faq-title">
          <div className="landing-faq-inner">
            <div className="landing-section-head">
              <p className="landing-kicker">Questions</p>
              <h2 id="faq-title">Before you dive in.</h2>
              <p>Short answers to the things people usually ask before the first run.</p>
            </div>

            <div className="faq-grid">
              {FAQS.map((item) => (
                <details key={item.question} className="faq-item">
                  <summary>
                    <span>{item.question}</span>
                    <CaretDown size={18} weight="bold" aria-hidden="true" />
                  </summary>
                  <p>{item.answer}</p>
                </details>
              ))}
            </div>
          </div>
        </section>

        <section className="landing-final" aria-labelledby="final-title">
          <div className="landing-final-inner">
            <div>
              <p className="landing-kicker">The pool is open</p>
              <h2 id="final-title">Ready when your file is.</h2>
              <p>
                Sign in through Elysiaa SSO and send one document through the arcade.
              </p>
            </div>
            <Link className="btn btn-primary" href="/convert">
              Start a conversion
              <ArrowRight size={18} weight="bold" aria-hidden="true" />
            </Link>
          </div>
        </section>
      </main>

      <footer className="landing-footer">
        <div className="landing-footer-inner">
          <div>
            <Link className="brand" href="/">
              <span className="brand-badge">G</span>
              <span className="brand-lockup">
                <span className="brand-name">Graphia</span>
                <span className="brand-tag">Document arcade</span>
              </span>
            </Link>
            <p>Private document conversion for a small desk.</p>
          </div>
          <div className="landing-footer-links">
            <a href="#product">Product</a>
            <a href="#how">How it works</a>
            <Link href="/privacy">Privacy</Link>
            <Link href="/terms">Terms</Link>
            <Link href="/login?next=/convert">Sign in</Link>
          </div>
        </div>
        <div className="landing-footer-base">
          <span>Graphia</span>
          <span>Files leave at closing.</span>
        </div>
      </footer>
    </div>
  );
}
