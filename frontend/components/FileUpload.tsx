"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useDropzone } from "react-dropzone";
import { Progress } from "@/components/ui/progress";
import { uploadDocument } from "@/lib/api";
import { Upload, FileText, AlertCircle, CheckCircle2 } from "lucide-react";

const DEFAULT_MAX_UPLOAD_MB = process.env.NODE_ENV === "development" ? 100 : 32;
const MAX_UPLOAD_MB = Number(process.env.NEXT_PUBLIC_MAX_UPLOAD_MB ?? DEFAULT_MAX_UPLOAD_MB);

export function FileUpload() {
  const router = useRouter();
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string>("");

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (!acceptedFiles.length) return;
      const file = acceptedFiles[0];
      if (file.size > MAX_UPLOAD_MB * 1024 * 1024) {
        setError(
          `This file is ${Math.ceil(file.size / (1024 * 1024))} MB. The current upload limit is ${MAX_UPLOAD_MB} MB.`
        );
        setUploading(false);
        setProgress(0);
        setStatus("");
        return;
      }
      setError(null);
      setUploading(true);
      setStatus("Uploading document...");
      setProgress(15);

      try {
        setProgress(30);
        setStatus("Parsing and extracting text...");
        const result = await uploadDocument(file);
        setProgress(80);
        setStatus(`Indexed ${result.chunks_indexed} chunks across ${result.page_count} pages`);
        setProgress(100);
        setStatus("Complete — redirecting...");
        setTimeout(() => router.push(`/query?doc=${result.document_id}`), 600);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Upload failed. Please try again.");
        setUploading(false);
        setProgress(0);
        setStatus("");
      }
    },
    [router]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "image/png": [".png"],
      "image/jpeg": [".jpg", ".jpeg"],
    },
    maxFiles: 1,
    disabled: uploading,
  });

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div
        {...getRootProps()}
        className={`
          relative border-2 border-dashed rounded-xl p-12 text-center cursor-pointer
          transition-all duration-200 bg-white
          ${isDragActive
            ? "border-brand-blue bg-brand-blue-light"
            : "border-gray-200 hover:border-brand-blue hover:bg-brand-blue-light/40"
          }
          ${uploading ? "opacity-60 cursor-not-allowed pointer-events-none" : ""}
        `}
      >
        <input {...getInputProps()} />

        <div className="flex flex-col items-center gap-4">
          <div
            className={`w-16 h-16 rounded-full flex items-center justify-center transition-colors
              ${isDragActive ? "bg-brand-blue" : "bg-brand-blue-light"}`}
          >
            {isDragActive ? (
              <Upload className="w-7 h-7 text-white" />
            ) : (
              <FileText className="w-7 h-7 text-brand-blue" />
            )}
          </div>

          <div>
            <p className="text-base font-semibold text-ink">
              {isDragActive
                ? "Release to upload"
                : "Drop your construction document here"}
            </p>
            <p className="text-sm text-ink-muted mt-1">
              or{" "}
              <span className="text-brand-blue font-medium hover:underline cursor-pointer">
                browse files
              </span>
              {" "}· PDF, PNG, JPG · Max {MAX_UPLOAD_MB} MB
            </p>
          </div>

          <div className="flex flex-wrap gap-2 justify-center">
            {["Spec Sheets", "RFIs", "Inspection Reports", "Building Plans"].map((t) => (
              <span
                key={t}
                className="text-xs px-2.5 py-1 rounded-full text-white font-medium"
                style={{ backgroundColor: "#0066CC" }}
              >
                {t}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Enterprise note */}
      <p className="mt-3 text-center text-xs text-ink-subtle">
        {MAX_UPLOAD_MB < 100 ? "Hosted uploads are currently capped below the app's local limit. " : ""}
        For files over {MAX_UPLOAD_MB} MB,{" "}
        <span className="text-brand-blue font-medium">contact us for enterprise ingestion pipeline.</span>
      </p>

      {/* Progress */}
      {uploading && (
        <div className="mt-5 space-y-2">
          <div className="flex justify-between text-xs text-ink-muted">
            <span className="flex items-center gap-1.5">
              {progress === 100 ? (
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
              ) : (
                <div className="w-3.5 h-3.5 border-2 border-brand-blue border-t-transparent rounded-full animate-spin" />
              )}
              {status}
            </span>
            <span className="font-medium text-ink">{progress}%</span>
          </div>
          <Progress value={progress} className="h-1.5 bg-gray-100" />
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="mt-4 flex items-start gap-2.5 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg p-3.5">
          <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0 text-red-500" />
          {error}
        </div>
      )}
    </div>
  );
}
