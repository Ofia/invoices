import { useState, useRef, useEffect } from 'react';
import { Upload, FileText, Loader2, AlertCircle } from 'lucide-react';
import { useWorkspace } from '../../contexts/WorkspaceContext';
import { documents } from '../../lib/api';
import type { PendingDocument } from '../../lib/api/types';

export default function DocumentsPage() {
  const { currentWorkspace } = useWorkspace();
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pendingDocuments, setPendingDocuments] = useState<PendingDocument[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Fetch documents when workspace changes
  useEffect(() => {
    if (currentWorkspace) {
      fetchDocuments();
    }
  }, [currentWorkspace]);

  const fetchDocuments = async () => {
    if (!currentWorkspace) return;

    try {
      setLoading(true);
      setError(null);
      const docs = await documents.list(currentWorkspace.id);
      setPendingDocuments(docs);
    } catch (err) {
      console.error('Failed to fetch documents:', err);
      setError('Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    handleFiles(files);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      handleFiles(files);
    }
  };

  const handleFiles = async (files: File[]) => {
    if (!currentWorkspace) {
      setError('Please select a workspace first');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      // Upload files one by one
      for (const file of files) {
        await documents.upload(currentWorkspace.id, file);
      }

      // Refresh document list
      await fetchDocuments();
    } catch (err: any) {
      console.error('Upload failed:', err);
      setError(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleProcess = async (docId: number) => {
    try {
      setError(null);
      await documents.process(docId);
      // Refresh list after processing
      await fetchDocuments();
    } catch (err: any) {
      console.error('Processing failed:', err);
      const errorData = err.response?.data;
      if (errorData?.error_type) {
        setError(`${errorData.error_type}: ${errorData.detail}`);
      } else {
        setError('Processing failed');
      }
    }
  };

  const handleReject = async (docId: number) => {
    if (!confirm('Are you sure you want to reject this document?')) return;

    try {
      setError(null);
      await documents.reject(docId);
      await fetchDocuments();
    } catch (err: any) {
      console.error('Rejection failed:', err);
      setError('Failed to reject document');
    }
  };

  const openFileBrowser = () => {
    fileInputRef.current?.click();
  };

  if (!currentWorkspace) {
    return (
      <div className="p-8">
        <div className="text-center py-12 border border-gray-200 rounded-xl bg-white">
          <AlertCircle className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">No workspace selected</p>
          <p className="text-sm text-gray-400 mt-1">
            Please create or select a workspace first
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      {/* Page Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Documents</h1>
          <p className="text-sm text-gray-500 mt-1">
            Upload and process invoice documents
          </p>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-100 rounded-xl animate-slide-down">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Upload Area - Small and Minimal */}
      <div className="mb-8">
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`
            relative border-2 border-dashed rounded-xl p-6 text-center
            transition-all duration-200 cursor-pointer
            ${
              isDragging
                ? 'border-gray-900 bg-gray-50'
                : 'border-gray-200 hover:border-gray-400'
            }
            ${uploading ? 'pointer-events-none' : ''}
          `}
          onClick={openFileBrowser}
        >
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.png,.jpg,.jpeg,.webp,.doc,.docx"
            onChange={handleFileSelect}
            className="hidden"
            disabled={uploading}
          />

          <div className="flex items-center justify-center gap-3">
            {uploading ? (
              <Loader2 className="w-5 h-5 text-gray-400 animate-spin" />
            ) : (
              <Upload className="w-5 h-5 text-gray-400" />
            )}
            <div className="text-sm">
              {uploading ? (
                <span className="text-gray-700 font-medium">Uploading...</span>
              ) : (
                <>
                  <span className="text-gray-900 font-medium">Click to upload</span>
                  <span className="text-gray-500"> or drag and drop</span>
                </>
              )}
            </div>
          </div>
          <p className="text-xs text-gray-400 mt-2">
            PDF, PNG, JPG, WEBP, DOC, DOCX (max 10MB)
          </p>
        </div>
      </div>

      {/* Documents Grid */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Pending Documents ({pendingDocuments.length})
        </h2>

        {loading ? (
          <div className="text-center py-12">
            <Loader2 className="w-8 h-8 text-gray-400 animate-spin mx-auto mb-3" />
            <p className="text-gray-500">Loading documents...</p>
          </div>
        ) : pendingDocuments.length > 0 ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
            {pendingDocuments.map((doc) => (
              <div
                key={doc.id}
                className="group relative p-4 bg-white border border-gray-200 rounded-xl hover:border-gray-900 hover:shadow-lg transition-all duration-300"
              >
                {/* Document Icon and Info */}
                <div className="flex items-start gap-3 mb-4">
                  <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center flex-shrink-0">
                    <FileText className="w-5 h-5 text-gray-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-medium text-gray-900 truncate">
                      {doc.filename}
                    </h3>
                    <p className="text-xs text-gray-500 mt-1">
                      Source: {doc.gmail_message_id ? 'Gmail' : 'Manual Upload'}
                    </p>
                    <p className="text-xs text-gray-400 mt-0.5">
                      {new Date(doc.uploaded_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>

                {/* Status Badge */}
                <div className="mb-3">
                  <span
                    className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium ${
                      doc.status === 'pending'
                        ? 'bg-yellow-50 text-yellow-800 border border-yellow-200'
                        : doc.status === 'processed'
                        ? 'bg-green-50 text-green-800 border border-green-200'
                        : 'bg-gray-50 text-gray-800 border border-gray-200'
                    }`}
                  >
                    {doc.status === 'pending'
                      ? 'Pending Review'
                      : doc.status === 'processed'
                      ? 'Processed'
                      : doc.status}
                  </span>
                </div>

                {/* Action Buttons */}
                {doc.status === 'pending' && (
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleProcess(doc.id)}
                      className="flex-1 px-3 py-1.5 text-xs font-medium text-white bg-gray-900 rounded-lg hover:bg-gray-800 transition-colors"
                    >
                      Process
                    </button>
                    <button
                      onClick={() => handleReject(doc.id)}
                      className="px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-200 rounded-lg hover:border-gray-900 transition-colors"
                    >
                      Reject
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12 border border-gray-200 rounded-xl bg-white">
            <FileText className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500">No pending documents</p>
            <p className="text-sm text-gray-400 mt-1">
              Upload or sync from Gmail to get started
            </p>
          </div>
        )}
      </div>

      {/* Animation styles */}
      <style>{`
        @keyframes slide-down {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .animate-slide-down {
          animation: slide-down 0.3s ease-out;
        }
      `}</style>
    </div>
  );
}
