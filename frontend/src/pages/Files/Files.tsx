import React, { useState, useEffect } from 'react';
import { FolderTree, FileCode, FileText, Search, Plus, Eye, RefreshCw, File } from 'lucide-react';
import { fileApi, WorkspaceFile } from '../../services/fileApi';

export const Files: React.FC = () => {
  const [files, setFiles] = useState<WorkspaceFile[]>([]);
  const [selectedFile, setSelectedFile] = useState<WorkspaceFile | null>(null);
  const [fileContent, setFileContent] = useState<string>('');
  const [searchFilter, setSearchFilter] = useState('');
  const [patternFilter, setPatternFilter] = useState('*.*');
  const [loading, setLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [newFilePath, setNewFilePath] = useState('');
  const [newFileContent, setNewFileContent] = useState('');

  const loadFiles = async () => {
    try {
      setLoading(true);
      const res = await fileApi.listFiles('.', patternFilter);
      setFiles(res.files || []);
    } catch (err) {
      console.error('Failed to load files', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFiles();
  }, [patternFilter]);

  const handleSelectFile = async (file: WorkspaceFile) => {
    setSelectedFile(file);
    try {
      const res = await fileApi.getFileContent(file.path);
      setFileContent(res.content);
    } catch (err) {
      setFileContent('Failed to read file content.');
    }
  };

  const handleCreateFile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newFilePath.trim()) return;
    try {
      await fileApi.createFile(newFilePath.trim(), newFileContent, true);
      setNewFilePath('');
      setNewFileContent('');
      setIsCreating(false);
      loadFiles();
    } catch (err) {
      console.error('Failed to create file', err);
    }
  };

  const filtered = files.filter((f) =>
    f.name.toLowerCase().includes(searchFilter.toLowerCase()) ||
    f.path.toLowerCase().includes(searchFilter.toLowerCase())
  );

  return (
    <div className="h-full flex flex-col bg-nexus-bg">
      {/* Header */}
      <div className="h-16 border-b border-nexus-border px-8 flex items-center justify-between bg-nexus-surface/50 shrink-0">
        <div className="flex items-center space-x-3">
          <FolderTree className="w-5 h-5 text-nexus-cyan" />
          <div>
            <h1 className="text-base font-bold text-white tracking-wide">
              Workspace Filesystem Explorer
            </h1>
            <span className="text-[11px] text-slate-400">
              {files.length} indexed files in local project root
            </span>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {/* Pattern Picker */}
          <select
            value={patternFilter}
            onChange={(e) => setPatternFilter(e.target.value)}
            className="bg-nexus-card border border-nexus-border text-xs rounded-xl px-2.5 py-1.5 text-slate-300 focus:outline-none focus:border-nexus-cyan"
          >
            <option value="*.*">All Files (*.*)</option>
            <option value="*.ts*">TypeScript (*.ts, *.tsx)</option>
            <option value="*.py">Python (*.py)</option>
            <option value="*.json">JSON (*.json)</option>
            <option value="*.md">Markdown (*.md)</option>
          </select>

          <button
            onClick={loadFiles}
            className="p-2 rounded-xl bg-nexus-surface hover:bg-nexus-card text-slate-400 hover:text-white border border-nexus-border transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>

          <button
            onClick={() => setIsCreating(true)}
            className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl bg-nexus-cyan text-slate-950 font-bold text-xs shadow-cyan-glow"
          >
            <Plus className="w-4 h-4" />
            <span>New File</span>
          </button>
        </div>
      </div>

      {/* Split Layout: File Tree & Content Preview */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left List */}
        <div className="w-80 border-r border-nexus-border flex flex-col bg-nexus-surface/30 shrink-0">
          <div className="p-3 border-b border-nexus-border">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-2.5" />
              <input
                type="text"
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                placeholder="Search filenames..."
                className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-nexus-card border border-nexus-border text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-nexus-cyan"
              />
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {filtered.map((file, idx) => {
              const isSelected = selectedFile?.path === file.path;
              return (
                <div
                  key={idx}
                  onClick={() => handleSelectFile(file)}
                  className={`p-2.5 rounded-xl cursor-pointer text-xs flex items-center justify-between transition-all ${
                    isSelected
                      ? 'bg-nexus-cyan/15 text-nexus-cyan border border-nexus-cyan/40 font-semibold'
                      : 'hover:bg-nexus-hover text-slate-300 border border-transparent'
                  }`}
                >
                  <div className="flex items-center space-x-2 truncate">
                    {file.name.endsWith('.ts') || file.name.endsWith('.tsx') ? (
                      <FileCode className="w-4 h-4 text-blue-400 shrink-0" />
                    ) : file.name.endsWith('.py') ? (
                      <FileCode className="w-4 h-4 text-yellow-400 shrink-0" />
                    ) : file.name.endsWith('.md') ? (
                      <FileText className="w-4 h-4 text-emerald-400 shrink-0" />
                    ) : (
                      <File className="w-4 h-4 text-slate-400 shrink-0" />
                    )}
                    <span className="truncate">{file.name}</span>
                  </div>
                  <span className="text-[10px] font-mono text-slate-500 shrink-0 ml-2">
                    {file.sizeBytes > 1024 ? `${Math.round(file.sizeBytes / 1024)} KB` : `${file.sizeBytes} B`}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Preview */}
        <div className="flex-1 flex flex-col bg-nexus-bg overflow-hidden">
          {selectedFile ? (
            <div className="h-full flex flex-col">
              <div className="h-12 border-b border-nexus-border px-6 flex items-center justify-between bg-nexus-card/50">
                <div className="flex items-center space-x-2 font-mono text-xs text-slate-300">
                  <Eye className="w-4 h-4 text-nexus-cyan" />
                  <span className="text-white font-bold">{selectedFile.name}</span>
                  <span className="text-slate-500">({selectedFile.path})</span>
                </div>
                <span className="text-[11px] font-mono text-slate-400">
                  ~{Math.round(fileContent.length / 4)} tokens
                </span>
              </div>
              <div className="flex-1 overflow-auto p-4 bg-nexus-card/30 font-mono text-xs text-slate-200">
                <pre className="leading-relaxed whitespace-pre-wrap">{fileContent}</pre>
              </div>
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-slate-500 space-y-2 p-8 text-center">
              <FolderTree className="w-12 h-12 text-slate-700" />
              <p className="text-sm font-medium text-slate-400">Select a file from the workspace to preview</p>
              <p className="text-xs text-slate-600 max-w-sm">
                Nexus File Agent continuously indexes and monitors changes for context synthesis.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* New File Modal */}
      {isCreating && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <form onSubmit={handleCreateFile} className="glass-panel w-full max-w-md rounded-2xl border border-nexus-cyan/40 p-6 space-y-4 shadow-cyan-glow">
            <h3 className="text-base font-bold text-white tracking-wide">
              Create New Workspace File
            </h3>
            <div>
              <label className="text-xs font-semibold text-slate-400 block mb-1">File Relative Path</label>
              <input
                type="text"
                value={newFilePath}
                onChange={(e) => setNewFilePath(e.target.value)}
                placeholder="e.g. scratch/demo_script.py"
                className="w-full px-3 py-2 rounded-xl bg-nexus-surface border border-nexus-border text-xs text-white focus:outline-none focus:border-nexus-cyan"
                required
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-400 block mb-1">Initial Content</label>
              <textarea
                value={newFileContent}
                onChange={(e) => setNewFileContent(e.target.value)}
                placeholder="# File contents..."
                rows={5}
                className="w-full px-3 py-2 rounded-xl bg-nexus-surface border border-nexus-border text-xs text-white focus:outline-none focus:border-nexus-cyan font-mono"
              />
            </div>
            <div className="flex items-center justify-end space-x-3 pt-2">
              <button
                type="button"
                onClick={() => setIsCreating(false)}
                className="px-4 py-2 rounded-xl bg-nexus-surface text-slate-300 border border-nexus-border text-xs"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-5 py-2 rounded-xl bg-nexus-cyan text-slate-950 font-bold text-xs shadow-cyan-glow"
              >
                Write to Disk
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
