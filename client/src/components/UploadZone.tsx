import { useCallback, useState } from 'react';

interface UploadZoneProps {
  onFileSelect: (file: File) => void;
  selectedFile: File | null;
  disabled?: boolean;
}

export default function UploadZone({ onFileSelect, selectedFile, disabled }: UploadZoneProps) {
  const [isDragOver, setIsDragOver] = useState(false);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled) setIsDragOver(true);
  }, [disabled]);

  const handleDragLeave = useCallback(() => {
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (disabled) return;

    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('video/')) {
      onFileSelect(file);
    }
  }, [disabled, onFileSelect]);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) onFileSelect(file);
  }, [onFileSelect]);

  const formatSize = (bytes: number): string => {
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => !disabled && document.getElementById('file-input')?.click()}
      className={`
        relative flex flex-col items-center justify-center
        rounded-2xl border-2 border-dashed p-10
        transition-all duration-300 cursor-pointer
        min-h-[220px]
        ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
        ${isDragOver
          ? 'border-emerald bg-emerald/5 scale-[1.02]'
          : selectedFile
            ? 'border-emerald/50 bg-bg-card'
            : 'border-border hover:border-emerald/40 hover:bg-bg-card/50'
        }
      `}
    >
      <input
        id="file-input"
        type="file"
        accept="video/*"
        className="hidden"
        onChange={handleFileInput}
        disabled={disabled}
      />

      {selectedFile ? (
        <div className="flex flex-col items-center gap-3 animate-fade-in">
          {/* Video icon */}
          <div className="w-14 h-14 rounded-xl bg-emerald/10 flex items-center justify-center">
            <svg className="w-7 h-7 text-emerald" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="m15.75 10.5 4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 0 0 2.25-2.25v-9a2.25 2.25 0 0 0-2.25-2.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25Z" />
            </svg>
          </div>
          <div className="text-center">
            <p className="text-text-primary font-medium truncate max-w-[280px]">{selectedFile.name}</p>
            <p className="text-text-muted text-sm mt-1">{formatSize(selectedFile.size)}</p>
          </div>
          <p className="text-emerald text-xs mt-1">Click to change file</p>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-4">
          {/* Upload cloud icon */}
          <div className={`w-16 h-16 rounded-2xl flex items-center justify-center transition-colors duration-300 ${isDragOver ? 'bg-emerald/20' : 'bg-bg-card'}`}>
            <svg className={`w-8 h-8 transition-colors duration-300 ${isDragOver ? 'text-emerald' : 'text-text-muted'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 16.5V9.75m0 0 3 3m-3-3-3 3M6.75 19.5a4.5 4.5 0 0 1-1.41-8.775 5.25 5.25 0 0 1 10.233-2.33 3 3 0 0 1 3.758 3.848A3.752 3.752 0 0 1 18 19.5H6.75Z" />
            </svg>
          </div>
          <div className="text-center">
            <p className="text-text-secondary font-medium">Drop your video here</p>
            <p className="text-text-muted text-sm mt-1">or click to browse</p>
          </div>
        </div>
      )}
    </div>
  );
}
