import { request } from './api';

export interface WorkspaceFile {
  name: string;
  path: string;
  sizeBytes: number;
  isDir: boolean;
  modified: number;
}

export interface WorkspaceFilesResponse {
  directory: string;
  pattern: string;
  count: number;
  files: WorkspaceFile[];
}

export const fileApi = {
  listFiles: (dir = '.', pattern = '*.*'): Promise<WorkspaceFilesResponse> => {
    return request<WorkspaceFilesResponse>(`/api/files?dir=${encodeURIComponent(dir)}&pattern=${encodeURIComponent(pattern)}`);
  },

  getFileContent: (path: string): Promise<{ success: boolean; content: string; path: string; size: number }> => {
    return request<{ success: boolean; content: string; path: string; size: number }>(`/api/files/content?path=${encodeURIComponent(path)}`);
  },

  createFile: (filepath: string, content: string, overwrite = true): Promise<any> => {
    return request<any>('/api/files', {
      method: 'POST',
      body: JSON.stringify({ filepath, content, overwrite }),
    });
  },
};
