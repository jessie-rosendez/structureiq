import { FileUpload } from "@/components/FileUpload";
import { Shield, Layers, CheckSquare, BarChart2 } from "lucide-react";

const features = [
  {
    icon: Layers,
    title: "Two-Layer RAG",
    description: "Every query retrieves from your document AND our compliance standards KB simultaneously.",
  },
  {
    icon: Shield,
    title: "Hallucination Guards",
    description: "Source-grounded answers only. Confidence scores flag uncertain determinations.",
  },
  {
    icon: CheckSquare,
    title: "4 Standards",
    description: "ADA 2010 · OSHA 1926 · IBC 2021 · ASHRAE 90.1 — cross-referenced on every query.",
  },
  {
    icon: BarChart2,
    title: "Full Reports",
    description: "Automated compliance reports across all standards with citations and risk scoring.",
  },
];

export default function Home() {
  return (
    <div className="min-h-screen bg-surface-secondary">
      {/* Top nav bar */}
      <header className="bg-white border-b border-border">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 bg-brand-blue rounded flex items-center justify-center">
              <span className="text-white text-xs font-bold">SQ</span>
            </div>
            <span className="font-semibold text-ink text-sm tracking-tight">StructureIQ</span>
            <span className="text-border">|</span>
            <span className="text-xs text-ink-muted">AEC Compliance Intelligence</span>
          </div>
          <div className="text-xs text-ink-subtle">
            Powered by Vertex AI · Gemini 2.0 Flash
          </div>
        </div>
      </header>

      {/* Hero section */}
      <div className="bg-white border-b border-border">
        <div className="max-w-6xl mx-auto px-6 py-14">
          <div className="max-w-2xl">
            <div className="inline-flex items-center bg-brand-blue-light border border-brand-blue-mid rounded-full px-3 py-1 text-xs font-medium text-brand-blue mb-5">
              Grounded · Cited · Auditable
            </div>
            <h1 className="text-4xl font-bold text-ink tracking-tight leading-tight">
              Construction Document<br />
              <span className="text-brand-blue">Compliance Analysis</span>
            </h1>
            <p className="text-ink-secondary text-lg mt-4 leading-relaxed">
              Upload a specification sheet, RFI, or inspection report. Get compliance analysis
              grounded against ADA, OSHA, IBC, and ASHRAE standards — with citations and
              confidence scores on every finding.
            </p>
          </div>
        </div>
      </div>

      {/* Upload card */}
      <div className="max-w-6xl mx-auto px-6 py-10">
        <div className="bg-white rounded-2xl border border-border shadow-card-lg p-10">
          <div className="max-w-2xl mx-auto">
            <h2 className="text-lg font-semibold text-ink text-center mb-1">
              Upload Document
            </h2>
            <p className="text-sm text-ink-muted text-center mb-8">
              Supports construction PDFs, spec sheets, inspection reports, and plan images.
            </p>
            <FileUpload />
          </div>
        </div>

        {/* Feature grid */}
        <div className="grid grid-cols-4 gap-4 mt-8">
          {features.map(({ icon: Icon, title, description }) => (
            <div
              key={title}
              className="bg-white rounded-xl border border-border shadow-card p-5 transition-colors group"
            >
              <div className="w-9 h-9 bg-brand-blue-light rounded-lg flex items-center justify-center mb-3 group-hover:bg-brand-blue transition-colors">
                <Icon className="w-4 h-4 text-brand-blue group-hover:text-white transition-colors" />
              </div>
              <p className="font-semibold text-ink text-sm">{title}</p>
              <p className="text-xs text-ink-muted mt-1.5 leading-relaxed">{description}</p>
            </div>
          ))}
        </div>

        {/* Standards badges */}
        <div className="mt-6 flex items-center justify-center gap-3 flex-wrap">
          {["ADA Standards 2010", "OSHA 29 CFR 1926", "IBC 2021", "ASHRAE 90.1 2019"].map((s) => (
            <span
              key={s}
              className="text-xs font-medium text-white rounded-full px-3 py-1.5"
              style={{ backgroundColor: "#0066CC" }}
            >
              {s}
            </span>
          ))}
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-border bg-white mt-8">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between text-xs text-ink-subtle">
          <span>StructureIQ · Internal Compliance Tool</span>
        </div>
      </footer>
    </div>
  );
}
