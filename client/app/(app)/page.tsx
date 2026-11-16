import UploadPanel from "@/components/converter/UploadPanel";
import { CompassIcon, LaurelIcon, ScrollIcon } from "@/components/scrapbook/icons";
import { PaperNote, RouteMap, TapeStrip } from "@/components/scrapbook/Ornaments";

export default function HomePage() {
  return (
    <div className="home">
      <section className="journal-spread">
        <div className="journal-page journal-page--left">
          <div className="folio-line">
            <span className="ink-stamp">Field notes</span>
            <span className="folio-number">Expedition No. 07</span>
          </div>

          <h1 className="display">
            Send a document
            <br />
            <em>on a journey.</em>
          </h1>
          <p className="lede">
            It leaves as a Word file, a PDF, a page of text, or an image. It comes back
            transformed. You keep the ticket, follow the route, and collect the result.
          </p>

          <div className="route-wrap">
            <RouteMap stage={0} />
          </div>

          <dl className="stat-row">
            <div>
              <dt>Weight</dt>
              <dd>25 MB</dd>
            </div>
            <div>
              <dt>Rest</dt>
              <dd>24 hours</dd>
            </div>
            <div>
              <dt>Method</dt>
              <dd>α β γ</dd>
            </div>
          </dl>

          <PaperNote className="hero-note" rotate={-1.2}>
            The browser sends the file straight to private storage. The API handles the
            ticket, and the processor does the work.
          </PaperNote>
        </div>

        <div className="journal-page journal-page--right">
          <TapeStrip className="tape--top-left" rotate={-6} />
          <TapeStrip className="tape--top-right" rotate={4} />
          <UploadPanel />
          <p className="margin-scribble">one document, one method, one ticket</p>
        </div>
      </section>

      <section className="method" aria-labelledby="method-title">
        <div className="method-head">
          <p className="eyebrow">The method</p>
          <h2 id="method-title" className="method-title">
            Three stages, kept together by a ticket.
          </h2>
        </div>

        <ol className="method-grid">
          <li className="method-step">
            <span className="method-glyph">α</span>
            <ScrollIcon className="method-icon" />
            <h3>Dispatch</h3>
            <p>
              Choose a file and a method. The API signs a direct upload to R2, so the
              document never passes through the web server.
            </p>
          </li>
          <li className="method-step">
            <span className="method-glyph">β</span>
            <CompassIcon className="method-icon" />
            <h3>Passage</h3>
            <p>
              The processor claims the job atomically, runs the right engine, and marks the
              ticket as it moves. The page can be left open or returned to later.
            </p>
          </li>
          <li className="method-step">
            <span className="method-glyph">γ</span>
            <LaurelIcon className="method-icon" />
            <h3>Homecoming</h3>
            <p>
              The result is stored under a fresh key. A short-lived signed link brings it
              back, and the objects rest until they expire.
            </p>
          </li>
        </ol>
      </section>
    </div>
  );
}
