import React, { useRef, useState } from 'react';
import { 
  Files, 
  Upload, 
  Trash2, 
  ArrowUpRight, 
  FileText, 
  FileSpreadsheet, 
  FileCode, 
  File, 
  CheckCircle2, 
  Eye,
  ShieldCheck
} from 'lucide-react';
import { FileItem } from '../types';
import { formatFileSize, formatDate } from '../utils/formatters';
import { Modal } from '../components/ui/Modal';

interface FilesPageProps {
  files: FileItem[];
  onUploadFile: (file: File) => Promise<void>;
  onDeleteFile: (fileId: string) => Promise<void>;
  onUseInTask: (file: FileItem) => void;
  loading: boolean;
}

const getFileIcon = (fileType: string) => {
  switch (fileType.toLowerCase()) {
    case 'csv':
    case 'xlsx':
      return <FileSpreadsheet className="w-5 h-5 text-blue-400" />;
    case 'pdf':
    case 'docx':
    case 'txt':
    case 'md':
      return <FileText className="w-5 h-5 text-purple-400" />;
    case 'py':
    case 'cpp':
    case 'java':
    case 'js':
    case 'ts':
    case 'sql':
      return <FileCode className="w-5 h-5 text-emerald-400" />;
    default:
      return <File className="w-5 h-5 text-slate-400" />;
  }
};

export const FilesPage: React.FC<FilesPageProps> = ({
  files,
  onUploadFile,
  onDeleteFile,
  onUseInTask,
  loading
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<FileItem | null>(null);
  const [dragOver, setDragOver] = useState(false);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      for (const f of Array.from(e.dataTransfer.files)) {
        onUploadFile(f);
      }
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      for (const f of Array.from(e.target.files)) {
        onUploadFile(f);
      }
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-8 max-w-5xl mx-auto space-y-8 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Workspace File Repository</h2>
          <p className="text-xs text-slate-400 mt-1">
            Secure local repository of uploaded datasets, spreadsheets, and document artifacts.
          </p>
        </div>

        <div>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            onChange={handleInputChange}
            className="hidden"
            accept=".csv,.xlsx,.json,.pdf,.docx,.txt,.py,.sql,.cpp,.java,.js,.ts"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-medium rounded-xl shadow-lg shadow-blue-600/20 transition-all border border-blue-400/30"
          >
            <Upload className="w-4 h-4" />
            <span>Upload Files</span>
          </button>
        </div>
      </div>

      {/* Drag and Drop Zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-3xl p-8 text-center cursor-pointer transition-all ${
          dragOver 
            ? 'border-blue-500 bg-blue-500/10' 
            : 'border-slate-800 bg-[#090d15] hover:border-slate-700 hover:bg-slate-900/40'
        }`}
      >
        <div className="w-12 h-12 rounded-2xl bg-blue-500/10 border border-blue-500/20 text-blue-400 flex items-center justify-center mx-auto mb-3">
          <Upload className="w-6 h-6" />
        </div>
        <h4 className="text-sm font-semibold text-slate-200">
          Click or Drag files to attach
        </h4>
        <p className="text-xs text-slate-500 mt-1">
          Supports CSV, XLSX, JSON, PDF, DOCX, TXT, and Source Code up to 25 MB
        </p>
        <div className="flex items-center justify-center gap-2 text-[11px] text-emerald-400/80 font-mono mt-3">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Strict client-side isolation • Never executed automatically</span>
        </div>
      </div>

      {/* Files List */}
      <div className="space-y-3">
        <div className="flex items-center justify-between text-xs text-slate-400">
          <span className="font-mono uppercase font-semibold tracking-wider">
            Repository Files ({files.length})
          </span>
        </div>

        {files.length === 0 ? (
          <div className="glass-card p-8 rounded-2xl text-center text-slate-500 text-xs">
            No files in workspace. Upload a dataset or run the demo to populate files.
          </div>
        ) : (
          <div className="space-y-2">
            {files.map((file) => (
              <div
                key={file.id}
                className="glass-card p-4 rounded-xl flex items-center justify-between hover:border-slate-700 transition-all"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div className="p-2.5 rounded-xl bg-slate-800/80 border border-slate-700/60 flex-shrink-0">
                    {getFileIcon(file.file_type)}
                  </div>
                  <div className="min-w-0">
                    <h4 className="text-xs font-semibold text-slate-200 truncate">{file.filename}</h4>
                    <div className="flex items-center gap-2 text-[11px] text-slate-400 font-mono mt-0.5">
                      <span className="uppercase text-blue-400">{file.file_type}</span>
                      <span>•</span>
                      <span>{formatFileSize(file.file_size)}</span>
                      <span>•</span>
                      <span>{formatDate(file.created_at)}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 flex-shrink-0">
                  <span className="inline-flex items-center gap-1 text-[11px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                    <CheckCircle2 className="w-3 h-3" /> Ready
                  </span>

                  <button
                    onClick={() => setSelectedFile(file)}
                    className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors"
                    title="Inspect file metadata"
                  >
                    <Eye className="w-4 h-4" />
                  </button>

                  <button
                    onClick={() => onUseInTask(file)}
                    className="flex items-center gap-1 px-2.5 py-1 bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 border border-blue-500/30 rounded-lg text-xs font-medium transition-colors"
                    title="Use in new task"
                  >
                    <span>Use in Task</span>
                    <ArrowUpRight className="w-3 h-3" />
                  </button>

                  <button
                    onClick={() => onDeleteFile(file.id)}
                    className="p-1.5 text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors"
                    title="Delete file"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* File Inspector Modal */}
      <Modal
        isOpen={Boolean(selectedFile)}
        onClose={() => setSelectedFile(null)}
        title={selectedFile?.filename || 'File Details'}
        subtitle="File Metadata & Extraction Summary"
        maxWidth="md"
      >
        {selectedFile && (
          <div className="space-y-4 text-xs">
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2 font-mono">
              <div className="flex justify-between">
                <span className="text-slate-500">File Type:</span>
                <span className="text-slate-200 uppercase">{selectedFile.file_type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">File Size:</span>
                <span className="text-slate-200">{formatFileSize(selectedFile.file_size)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Uploaded:</span>
                <span className="text-slate-200">{formatDate(selectedFile.created_at)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Local Path:</span>
                <span className="text-slate-400 truncate max-w-[200px]" title={selectedFile.file_path}>
                  {selectedFile.file_path}
                </span>
              </div>
            </div>

            {selectedFile.metadata && (
              <div className="space-y-1.5">
                <span className="text-slate-400 font-mono uppercase text-[10px]">Extracted Metadata</span>
                <pre className="p-3 bg-slate-950 border border-slate-800 rounded-xl overflow-x-auto text-[11px] font-mono text-cyan-300">
                  {JSON.stringify(selectedFile.metadata, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};
