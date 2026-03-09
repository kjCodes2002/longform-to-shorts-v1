import type { ProcessVideoResponse, PipelineSettings } from '../types';

export async function processVideo(
  file: File,
  settings: PipelineSettings,
  onProgress?: (step: string) => void,
): Promise<ProcessVideoResponse> {
  const formData = new FormData();
  formData.append('video', file);
  formData.append('n_answers', String(settings.nAnswers));
  formData.append('model', settings.model);
  formData.append('temperature', String(settings.temperature));

  onProgress?.('uploading');

  const response = await fetch('/api/process-video', {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(
      Array.isArray(error.detail)
        ? error.detail.join(', ')
        : error.detail || `Server error: ${response.status}`
    );
  }

  return response.json();
}

export function getClipUrl(downloadUrl: string): string {
  return downloadUrl;
}
