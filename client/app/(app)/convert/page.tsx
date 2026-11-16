import { Drop, DownloadSimple, Joystick, Ticket } from "@phosphor-icons/react/dist/ssr";

import { PoolBubbles } from "@/components/arcade/ArcadeBits";
import UploadPanel from "@/components/converter/UploadPanel";

export default function HomePage() {
  return (
    <div className="home">
      <section className="hero-cabinet">
        <div className="hero-screen">
          <PoolBubbles />
          <span className="screen-watermark" aria-hidden="true">
            G
          </span>
          <div className="screen-kicker">
            <span className="status-dot" aria-hidden="true" />
            Pool&apos;s open · Document arcade
          </div>

          <h1 className="display">
            Make a
            <br />
            <span>splash</span>
          </h1>

          <p className="lede">
            Drop a document into the deep end. Pick a move. Climb out with a different
            file.
          </p>

          <a className="btn btn-primary hero-cta" href="#control-deck">
            Choose a file
          </a>

          <dl className="hero-stats">
            <div>
              <dt>Max file</dt>
              <dd>25 MB</dd>
            </div>
            <div>
              <dt>Locker</dt>
              <dd>24 hours</dd>
            </div>
            <div>
              <dt>Modes</dt>
              <dd>5</dd>
            </div>
          </dl>

          <div className="lane-lines" aria-hidden="true">
            <span />
            <span />
            <span />
            <span />
          </div>

          <div className="screen-note">
            <Drop size={24} weight="bold" aria-hidden="true" />
            <span>No app server touches the file. It goes straight to the locker.</span>
          </div>
        </div>

        <div className="control-deck" id="control-deck">
          <div className="deck-head">
            <span className="deck-label">Control deck</span>
            <span className="deck-lights" aria-hidden="true">
              <i />
              <i />
              <i />
            </span>
          </div>
          <UploadPanel />
        </div>
      </section>

      <section className="mode-strip" aria-labelledby="mode-title">
        <div className="mode-strip-head">
          <p className="strip-label">How the pool works</p>
          <h2 id="mode-title">Three moves. No queue.</h2>
        </div>

        <ol className="mode-grid">
          <li className="mode-step">
            <span className="mode-number">01</span>
            <Drop className="mode-icon" size={32} weight="bold" aria-hidden="true" />
            <h3>Drop it</h3>
            <p>
              Choose a file. The API signs a direct upload to R2, so the document never
              passes through the web server.
            </p>
          </li>
          <li className="mode-step">
            <span className="mode-number">02</span>
            <Joystick className="mode-icon" size={32} weight="bold" aria-hidden="true" />
            <h3>Run it</h3>
            <p>
              The processor claims the job, runs the conversion, and lights up the lane
              meter as it moves.
            </p>
          </li>
          <li className="mode-step">
            <span className="mode-number">03</span>
            <DownloadSimple className="mode-icon" size={32} weight="bold" aria-hidden="true" />
            <h3>Take it</h3>
            <p>
              A temporary signed link brings the result back. The locker clears the files
              when the clock runs out.
            </p>
          </li>
        </ol>

        <div className="mode-stamp" aria-hidden="true">
          <Ticket size={24} weight="bold" />
          <span>One file in. One file out.</span>
        </div>
      </section>
    </div>
  );
}
