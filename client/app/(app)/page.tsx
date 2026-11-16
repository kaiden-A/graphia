import UploadPanel from "@/components/converter/UploadPanel";

export default function HomePage() {
  return (
    <div className="home">
      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">Document desk · Est. 2026</p>
          <h1 className="display">
            Convert the thing.
            <br />
            <em>Keep the thread.</em>
          </h1>
          <p className="lede">
            Drop in a Word document, a PDF, a text file, Markdown, or an image. Pick the
            operation, leave the desk, and come back to a finished file. The processor works
            in the background.
          </p>

          <dl className="stat-row">
            <div>
              <dt>Max file</dt>
              <dd>25 MB</dd>
            </div>
            <div>
              <dt>Stored for</dt>
              <dd>24 hours</dd>
            </div>
            <div>
              <dt>Processing</dt>
              <dd>Async</dd>
            </div>
          </dl>

          <div className="hero-note">
            <span className="hero-note-mark" aria-hidden="true" />
            <p>
              Files go directly from your browser to private object storage. They do not pass
              through the web server, and download links are temporary.
            </p>
          </div>
        </div>

        <UploadPanel />
      </section>

      <section className="how" aria-labelledby="how-title">
        <div className="how-head">
          <p className="eyebrow">The shape of it</p>
          <h2 id="how-title" className="how-title">
            One document, three quiet steps.
          </h2>
        </div>
        <ol className="how-grid">
          <li>
            <span className="how-index mono">01</span>
            <h3>Drop and choose</h3>
            <p>
              The browser asks the API for a signed upload, then sends the file straight to R2.
              No giant request through the app server.
            </p>
          </li>
          <li>
            <span className="how-index mono">02</span>
            <h3>Leave the desk</h3>
            <p>
              The API creates a ticket and hands the job to the processor. The processor claims
              it atomically and runs the conversion engine.
            </p>
          </li>
          <li>
            <span className="how-index mono">03</span>
            <h3>Take the file</h3>
            <p>
              Poll the ticket, download through a short-lived signed URL, and let the files
              expire when their time is up.
            </p>
          </li>
        </ol>
      </section>
    </div>
  );
}
