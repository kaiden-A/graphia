import UploadPanel from "@/components/converter/UploadPanel";

const STEPS = [
  {
    title: "Upload direct",
    text: "The browser sends the file to private storage with a signed URL.",
  },
  {
    title: "The processor runs",
    text: "A temporary copy is converted while you are free to leave the page.",
  },
  {
    title: "Collect the result",
    text: "Sign in if you are a guest, then ask for a signed download link while the locker holds it.",
  },
];

export default async function ConvertPage({
  searchParams,
}: {
  searchParams: Promise<{ operation?: string | string[] }>;
}) {
  const params = await searchParams;
  const initialOperation =
    typeof params.operation === "string" ? params.operation : null;

  return (
    <div className="convert-page">
      <section className="convert-intro" aria-labelledby="convert-title">
        <div className="intro-copy">
          <p className="eyebrow caption-3">Converter</p>
          <h1 id="convert-title" className="heading-2">
            Start a run.
          </h1>
          <p className="body-2">
            Choose a document. The matching mode is picked for its extension, and you can
            change it before the run. The upload goes straight to private storage, and the
            ticket keeps the rest of the story.
          </p>
        </div>

        <dl className="intro-stats caption-4">
          <div>
            <dt>Max file</dt>
            <dd className="title-1">25 MB</dd>
          </div>
          <div>
            <dt>Locker</dt>
            <dd className="title-1">24 hours</dd>
          </div>
          <div>
            <dt>Modes</dt>
            <dd className="title-1">10</dd>
          </div>
        </dl>
      </section>

      <UploadPanel initialOperation={initialOperation} />

      <section className="convert-steps" aria-labelledby="steps-title">
        <div className="section-head section-head--tight">
          <div>
            <p className="eyebrow caption-3">After the upload</p>
            <h2 id="steps-title" className="heading-5">
              The ticket does the rest.
            </h2>
          </div>
        </div>

        <ol className="steps">
          {STEPS.map((step, index) => (
            <li className="step" key={step.title}>
              <span className="step-index caption-4">
                {String(index + 1).padStart(2, "0")}
              </span>
              <h3 className="title-2">{step.title}</h3>
              <p className="body-5">{step.text}</p>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}
