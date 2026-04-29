import React, { useState, useCallback } from "react";
import { meetingsApi } from "../api/client";

interface Props {
  meetingId: string;
  onSuccess: () => void;
}

export default function TranscriptUploader({ meetingId, onSuccess }: Props) {
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [requireConfirm, setRequireConfirm] = useState(true);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) setFile(f);
  }, []);

  const handleSubmit = async () => {
    if (!text.trim() && !file) {
      setMessage("Please provide a transcript or audio file.");
      return;
    }
    setLoading(true);
    setMessage(null);
    try {
      if (file) {
        await meetingsApi.uploadAudio(meetingId, file);
      } else {
        await meetingsApi.uploadTranscript(meetingId, text, requireConfirm);
      }
      setMessage("✅ Transcript processed! Switching to Notes/Tasks tabs to see results.");
      setText("");
      setFile(null);
      onSuccess();
    } catch {
      setMessage("❌ Failed to process transcript. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-5">
      <h3 className="font-semibold text-gray-900 mb-4">Upload Transcript / Audio</h3>

      {/* Audio drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={`border-2 border-dashed rounded-lg p-6 text-center mb-4 transition-colors cursor-pointer ${
          dragging ? "border-blue-400 bg-blue-50" : "border-gray-300 hover:border-gray-400"
        }`}
        onClick={() => document.getElementById("audio-upload")?.click()}
      >
        <input
          id="audio-upload"
          type="file"
          accept=".mp3,.mp4,.wav,.m4a,.webm,.ogg"
          className="hidden"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
        />
        {file ? (
          <div className="text-sm text-gray-700">
            🎵 <strong>{file.name}</strong>
            <button
              onClick={(e) => { e.stopPropagation(); setFile(null); }}
              className="ml-2 text-red-400 hover:text-red-600"
            >
              ✕
            </button>
          </div>
        ) : (
          <div>
            <p className="text-gray-500 text-sm">Drop audio file here or click to browse</p>
            <p className="text-gray-400 text-xs mt-1">MP3, MP4, WAV, M4A, WebM, OGG</p>
          </div>
        )}
      </div>

      <div className="text-center text-sm text-gray-400 mb-4">— or paste transcript text —</div>

      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Paste your meeting transcript here..."
        rows={8}
        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      />

      <div className="flex items-center gap-2 mt-3">
        <input
          type="checkbox"
          id="require-confirm"
          checked={requireConfirm}
          onChange={(e) => setRequireConfirm(e.target.checked)}
          className="rounded"
        />
        <label htmlFor="require-confirm" className="text-sm text-gray-600">
          Require confirmation before syncing tasks to external systems
        </label>
      </div>

      {message && (
        <div className={`mt-3 px-4 py-2 rounded-lg text-sm ${
          message.startsWith("✅") ? "bg-green-50 text-green-700 border border-green-200" : "bg-red-50 text-red-700 border border-red-200"
        }`}>
          {message}
        </div>
      )}

      <button
        onClick={handleSubmit}
        disabled={loading || (!text.trim() && !file)}
        className="mt-4 w-full py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
      >
        {loading ? "Processing…" : "🚀 Process Transcript"}
      </button>
    </div>
  );
}
