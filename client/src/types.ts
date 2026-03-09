export interface ClipSegment {
  start: number;
  end: number;
}

export interface ClipResult {
  download_url: string;
  filename: string;
  segments: ClipSegment[];
}

export interface ProcessVideoResponse {
  status: string;
  clips: ClipResult[];
  errors: string[];
}

export interface PipelineSettings {
  nAnswers: number;
  model: string;
  temperature: number;
}

export type PipelineStep = 'idle' | 'uploading' | 'extracting' | 'transcribing' | 'highlighting' | 'clipping' | 'done' | 'error';
