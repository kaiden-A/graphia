import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, CaretDown, Check } from "@phosphor-icons/react/dist/ssr";

import LandingMotion from "@/components/brand/LandingMotion";
import Logo from "@/components/brand/Logo";
import TaglineReveal from "@/components/brand/TaglineReveal";

export const metadata: Metadata = {
  title: "Graphia — document conversion, privately run",
  description:
    "Turn Word documents, slide decks, spreadsheets, PDFs, Markdown, text, and images into the file you need. Uploads go straight to private storage, and every run returns a ticket you can read.",
};

const FORMATS = [
  {
    from: "DOCX",
    to: "PDF",
    note: "A Word document becomes a print ready PDF.",
    inputs: ".docx",
  },
  {
    from: "PPTX",
    to: "PDF",
    note: "A slide deck becomes a PDF handout.",
    inputs: ".pptx",
  },
  {
    from: "XLSX",
    to: "PDF",
    note: "A workbook is laid out as a paginated PDF.",
    inputs: ".xlsx",
  },
  {
    from: "IMG",
    to: "PDF",
    note: "One image is placed on a single PDF page.",
    inputs: ".png .jpg .webp .gif .bmp .tif",
  },
  {
    from: "MD",
    to: "PDF",
    note: "Markdown is rendered as a styled PDF.",
    inputs: ".md .markdown",
  },
  {
    from: "PDF",
    to: "MD",
    note: "Selectable text comes out page by page as Markdown.",
    inputs: ".pdf",
  },
  {
    from: "PDF",
    to: "TXT",
    note: "Selectable text comes out as one plain text file.",
    inputs: ".pdf",
  },
  {
    from: "PDF",
    to: "PDF",
    note: "A shared copy with lighter images and a smaller file.",
    inputs: ".pdf",
  },
  {
    from: "DOCX",
    to: "MD",
    note: "Headings, lists, and tables become Markdown. Images are omitted.",
    inputs: ".docx",
  },
  {
    from: "TXT",
    to: "MD",
    note: "Plain text becomes clean Markdown paragraphs.",
    inputs: ".txt",
  },
];

const BENEFITS = [
  {
    title: "Storage direct",
    text: "The browser uploads to private object storage with a signed URL. The web app never holds the file.",
  },
  {
    title: "A ticket, not a spinner",
    text: "Status, file sizes, the expiry, and the exact reason when a run stops.",
  },
  {
    title: "Leave after the upload",
    text: "The API answers as soon as the file lands. The processor works in the background.",
  },
  {
    title: "The original stays",
    text: "A run writes a new output file. The source is untouched until it expires.",
  },
];

const STEPS = [
  {
    title: "Send it",
    text: "Choose a file and a mode. The API signs a direct upload to private storage.",
  },
  {
    title: "Leave it",
    text: "The processor claims the run, converts the file, and updates the ticket on its own.",
  },
  {
    title: "Collect it",
    text: "Sign in if you are a guest, then ask for a signed download link while the locker holds the result.",
  },
];

const FLOW = [
  {
    name: "Browser",
    note: "Signed upload",
  },
  {
    name: "Private storage",
    note: "Input and output",
  },
  {
    name: "Processor",
    note: "Temporary copy",
  },
];

const FAQS = [
  {
    question: "What can I convert?",
    answer:
      "Word documents, slide decks, spreadsheets, PDFs, Markdown, text, and images — in the direction shown in the converter. PDFs can also be turned into plain text or made smaller.",
  },
  {
    question: "How large can a file be?",
    answer:
      "25 MB. The API checks the size and the file type before anything is stored.",
  },
  {
    question: "Who can use Graphia?",
    answer:
      "Anyone can start a guest run. Accounts are made through Elysiaa SSO with Zitadel; if registration is invite only, ask the owner. Signing in moves your guest runs to the account.",
  },
  {
    question: "Where do the files go?",
    answer:
      "Your browser uploads straight to private object storage with a signed URL. The web app never holds the file.",
  },
  {
    question: "Do I lose the original?",
    answer:
      "No. A run writes a new output file. The upload stays as it was until the locker clears it.",
  },
  {
    question: "How long are files kept?",
    answer:
      "24 hours by default. The exact expiry is printed on the run ticket, and you can delete a finished run sooner.",
  },
  {
    question: "What if a conversion fails?",
    answer:
      "The ticket keeps the reason. Password protected PDFs and scanned PDFs without selectable text are the usual causes.",
  },
  {
    question: "Does Graphia see my password?",
    answer:
      "No. Sign in happens on Zitadel. Graphia stores a session token and never receives your password.",
  },
];

export default function LandingPage() {
  return (
    <div className="landing">
      <LandingMotion />

      <a className="skip-link" href="#main-content">
        Skip to content
      </a>

      <header className="landing-nav">
        <div className="landing-nav-inner">
          <Link className="brand-link" href="/" aria-label="Graphia home">
            <Logo />
          </Link>

          <nav className="landing-links" aria-label="Sections">
            <a href="#formats">Formats</a>
            <a href="#why">Why this one</a>
            <a href="#how">How it works</a>
            <Link href="/cli-docs">CLI</Link>
            <a href="#questions">Questions</a>
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

      <main id="main-content">
        <section className="landing-hero" aria-labelledby="landing-title">
          <div className="hero-copy">
            <p className="eyebrow caption-3">Document conversion, privately run</p>
            <h1 id="landing-title" className="landing-title heading-1">
              A private press for everyday documents.
            </h1>
            <p className="landing-lede body-2">
              Turn Word documents, slide decks, spreadsheets, PDFs, Markdown, text, and images
              into the file you need. Uploads go straight to private storage, and every run
              returns a ticket you can read.
            </p>
            <div className="landing-cta-row">
              <Link className="btn btn-primary btn-large" href="/convert">
                Start a conversion
                <ArrowRight size={18} weight="bold" aria-hidden="true" />
              </Link>
              <a className="landing-text-link caption-1" href="#how">
                See how a run works
              </a>
            </div>
            <div className="landing-guest">
              <span className="caption-4">No account needed to convert.</span>
              <form action="/api/auth/guest?next=%2Fconvert" method="post">
                <button className="text-button text-button--accent caption-4" type="submit">
                  Continue as guest
                </button>
              </form>
            </div>
            <ul className="landing-proof caption-4">
              <li>25 MB per file</li>
              <li>10 modes</li>
              <li>Files expire in 24 hours</li>
            </ul>
          </div>

          <div
            className="specimen-frame"
            role="img"
            aria-label="Sample run ticket: a DOCX file converted to PDF and ready to collect."
          >
            <span className="crop crop--tl" aria-hidden="true" />
            <span className="crop crop--tr" aria-hidden="true" />
            <span className="crop crop--bl" aria-hidden="true" />
            <span className="crop crop--br" aria-hidden="true" />

            <div className="specimen">
              <div className="specimen-head">
                <span className="eyebrow caption-3">Sample run</span>
                <span className="specimen-stamp caption-3">Processed</span>
              </div>
              <p className="specimen-number caption-4">No. 8F2A1C</p>
              <p className="specimen-title heading-5">field notes.docx</p>
              <p className="specimen-mode caption-1">DOCX to PDF</p>

              <div className="perforation" aria-hidden="true" />

              <dl className="specimen-grid">
                <div>
                  <dt className="caption-4">Input</dt>
                  <dd className="title-3">184 KB</dd>
                </div>
                <div>
                  <dt className="caption-4">Output</dt>
                  <dd className="title-3">field notes.pdf</dd>
                </div>
                <div>
                  <dt className="caption-4">Started</dt>
                  <dd className="title-3">14:02</dd>
                </div>
                <div>
                  <dt className="caption-4">Locker</dt>
                  <dd className="title-3">24 hours</dd>
                </div>
              </dl>

              <div className="specimen-bar" aria-hidden="true">
                <span />
              </div>

              <div className="specimen-foot caption-4">
                <span>Ready to collect</span>
                <span>Expires in 24 hours</span>
              </div>
            </div>
          </div>
        </section>

        <section id="formats" className="landing-formats" aria-labelledby="formats-title">
          <div className="section-head" data-reveal>
            <div>
              <p className="eyebrow caption-3">
                <span className="eyebrow-index">01</span>The formats
              </p>
              <h2 id="formats-title" className="heading-3">
                Ten modes. Nothing to configure.
              </h2>
            </div>
            <p className="section-note body-5">
              Each mode does one job. Pick the pair that matches the file in your hand.
            </p>
          </div>

          <div className="format-table" data-reveal-stagger>
            {FORMATS.map((format, index) => (
              <div className="format-row" key={format.from + format.to}>
                <span className="format-index caption-4">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <span className="format-pair">
                  <span className="format-code caption-3">{format.from}</span>
                  <span className="format-arrow" aria-hidden="true">
                    →
                  </span>
                  <span className="format-code format-code--out caption-3">{format.to}</span>
                </span>
                <p className="format-note body-2">{format.note}</p>
                <span className="format-inputs caption-5">{format.inputs}</span>
              </div>
            ))}
          </div>
        </section>

        <section id="why" className="landing-benefits" aria-labelledby="benefits-title">
          <div className="section-head" data-reveal>
            <div>
              <p className="eyebrow caption-3">
                <span className="eyebrow-index">02</span>Why this one
              </p>
              <h2 id="benefits-title" className="heading-3">
                Small, private, and legible.
              </h2>
            </div>
            <p className="section-note body-5">
              Built for one desk and a few invited people, not for a public queue.
            </p>
          </div>

          <div className="benefit-grid" data-reveal-stagger>
            {BENEFITS.map((benefit, index) => (
              <article className="benefit" key={benefit.title}>
                <span className="benefit-index caption-4">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <h3 className="title-1">{benefit.title}</h3>
                <p className="body-5">{benefit.text}</p>
              </article>
            ))}
          </div>
        </section>

        <TaglineReveal
          className="landing-tagline"
          lines={[
            "Send the document you have.",
            "Keep the one you need.",
          ]}
        />
        <noscript>
          <style>{".tagline-reveal span{color:#f4ecdf}"}</style>
        </noscript>

        <section id="how" className="landing-how" aria-labelledby="how-title">
          <div className="section-head" data-reveal>
            <div>
              <p className="eyebrow caption-3">
                <span className="eyebrow-index">03</span>How it works
              </p>
              <h2 id="how-title" className="heading-3">
                Send it, leave it, collect it.
              </h2>
            </div>
            <p className="section-note body-5">
              The path is short because the architecture is.
            </p>
          </div>

          <ol className="steps" data-reveal-stagger>
            {STEPS.map((step, index) => (
              <li className="step" key={step.title}>
                <span className="step-index caption-4">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <h3 className="title-1">{step.title}</h3>
                <p className="body-5">{step.text}</p>
              </li>
            ))}
          </ol>
        </section>

        <section className="landing-privacy on-dark" aria-labelledby="privacy-title">
          <div className="privacy-inner" data-reveal>
            <div className="privacy-copy">
              <p className="eyebrow caption-3">
                <span className="eyebrow-index">04</span>Under the hood
              </p>
              <h2 id="privacy-title" className="heading-3">
                The file never sits on the web server.
              </h2>
              <p className="body-5">
                The browser uploads straight to private object storage. The processor takes a
                temporary copy, converts it, and deletes that copy when the run ends. The web
                app only ever sees metadata.
              </p>
              <p className="risk-line caption-1">
                <Check size={16} weight="bold" aria-hidden="true" />
                Delete a finished run from its ticket.
              </p>
            </div>

            <div className="flow" data-reveal-stagger>
              {FLOW.map((node, index) => (
                <div className="flow-item" key={node.name}>
                  {index > 0 ? (
                    <span className="flow-arrow" aria-hidden="true">
                      →
                    </span>
                  ) : null}
                  <div className="flow-node">
                    <span className="caption-4">
                      {String(index + 1).padStart(2, "0")}
                    </span>
                    <strong className="title-3">{node.name}</strong>
                    <span className="caption-4">{node.note}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="questions" className="landing-faq" aria-labelledby="faq-title">
          <div className="faq-inner">
            <div className="section-head" data-reveal>
              <div>
                <p className="eyebrow caption-3">
                  <span className="eyebrow-index">05</span>Questions
                </p>
                <h2 id="faq-title" className="heading-3">
                  The short answers.
                </h2>
              </div>
              <p className="section-note body-5">
                The things people usually ask before the first run.
              </p>
            </div>

            <div className="faq-grid" data-reveal-stagger>
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
          </div>
        </section>

        <section className="landing-final on-dark" aria-labelledby="final-title">
          <div className="final-inner" data-reveal>
            <div>
              <p className="eyebrow caption-3">Ready when you are</p>
              <h2 id="final-title" className="heading-2">
                Send the document. Keep the result.
              </h2>
              <p className="body-5">
                Start as a guest, or sign in through Elysiaa SSO. One file through the press.
              </p>
            </div>
            <Link className="btn btn-primary btn-large" href="/convert">
              Start a conversion
              <ArrowRight size={18} weight="bold" aria-hidden="true" />
            </Link>
          </div>
        </section>
      </main>

      <footer className="landing-footer">
        <div className="footer-inner">
          <div className="footer-brand">
            <Link className="brand-link" href="/" aria-label="Graphia home">
              <Logo />
            </Link>
            <p className="body-6">Private document conversion for a small desk.</p>
          </div>

          <nav className="footer-links caption-5" aria-label="Footer">
            <a href="#formats">Formats</a>
            <a href="#how">How it works</a>
            <Link href="/cli-docs">CLI</Link>
            <a href="#questions">Questions</a>
            <Link href="/privacy">Privacy</Link>
            <Link href="/terms">Terms</Link>
            <Link href="/login?next=/convert">Sign in</Link>
          </nav>
        </div>

        <div className="footer-base caption-5">
          <span>Graphia / Document atelier</span>
          <span>
            Mark:{" "}
            <a href="https://iconscout.com/unicons" rel="noreferrer">
              Unicons by IconScout
            </a>
          </span>
          <span>Files expire in 24 hours</span>
        </div>
      </footer>
    </div>
  );
}
