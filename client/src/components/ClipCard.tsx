import type { ClipResult } from '../types';
import { getClipUrl } from '../api/processVideo';

interface ClipCardProps {
  clip: ClipResult;
  index: number;
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}

export default function ClipCard({ clip, index }: ClipCardProps) {
  const totalDuration = clip.segments.reduce((sum, seg) => sum + (seg.end - seg.start), 0);

  return (
    <div
      className="group bg-bg-card rounded-2xl border border-border overflow-hidden
                 transition-all duration-300 hover:border-emerald/30 hover:bg-bg-card-hover
                 animate-slide-up"
      style={{ animationDelay: `${index * 100}ms`, animationFillMode: 'backwards' }}
    >
      {/* Video preview */}
      <div className="relative aspect-video bg-bg-secondary">
        <video
          src={getClipUrl(clip.download_url)}
          className="w-full h-full object-cover"
          controls
          preload="metadata"
        />
      </div>

      {/* Info */}
      <div className="p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-text-primary font-semibold text-sm">
            Highlight {index + 1}
          </h3>
          <span className="text-text-muted text-xs">
            {formatTime(totalDuration)}
          </span>
        </div>

        {/* Segments */}
        <div className="flex flex-wrap gap-2 mb-4">
          {clip.segments.map((seg, i) => (
            <span
              key={i}
              className="bg-emerald/10 text-emerald text-xs px-2.5 py-1 rounded-lg font-medium"
            >
              {formatTime(seg.start)} – {formatTime(seg.end)}
            </span>
          ))}
        </div>

        {/* Download button */}
        <a
          href={getClipUrl(clip.download_url)}
          download={clip.filename}
          className="flex items-center justify-center gap-2 w-full py-2.5 rounded-xl
                     bg-bg-secondary border border-border text-text-secondary text-sm font-medium
                     transition-all duration-200 hover:border-emerald/40 hover:text-emerald"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" />
          </svg>
          Download
        </a>
      </div>
    </div>
  );
}
