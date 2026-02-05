import { useState, useRef, useEffect } from 'react';
import { Upload, FileText, Loader2, AlertCircle, Mail, X } from 'lucide-react';
import { useWorkspace } from '../../contexts/WorkspaceContext';
import { documents, gmail } from '../../lib/api';
import type { PendingDocument } from '../../lib/api/types';

export default function DocumentsPage() {
  const { currentWorkspace } = useWorkspace();
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pendingDocuments, setPendingDocuments] = useState<PendingDocument[]>([]);
  const [showSyncModal, setShowSyncModal] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [selectedDays, setSelectedDays] = useState(7);
  const [syncSuccess, setSyncSuccess] = useState<string | null>(null);
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

  const handleGmailSync = async () => {
    if (!currentWorkspace) return;

    try {
      setSyncing(true);
      setError(null);
      setSyncSuccess(null);

      const result = await gmail.sync(currentWorkspace.id, selectedDays);

      setSyncSuccess(
        `Synced successfully! ${result.documents_created} new documents created from ${result.invoices_detected} invoice emails. ${result.duplicates_skipped} duplicates skipped.`
      );

      // Close modal and refresh documents
      setShowSyncModal(false);
      await fetchDocuments();
    } catch (err: any) {
      console.error('Gmail sync failed:', err);
      const errorData = err.response?.data;
      setError(errorData?.detail || 'Gmail sync failed');
      setShowSyncModal(false);
    } finally {
      setSyncing(false);
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
        <button
          onClick={() => setShowSyncModal(true)}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-gray-900 rounded-lg hover:bg-gray-800 transition-colors"
        >
          <Mail className="w-4 h-4" />
          Sync Gmail
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-100 rounded-xl animate-slide-down">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Success Message */}
      {syncSuccess && (
        <div className="mb-6 p-4 bg-green-50 border border-green-100 rounded-xl animate-slide-down">
          <p className="text-sm text-green-800">{syncSuccess}</p>
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

      {/* Gmail Sync Modal */}
      {showSyncModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4 animate-slide-up">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Sync Gmail</h3>
              <button
                onClick={() => setShowSyncModal(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6">
              <p className="text-sm text-gray-600 mb-4">
                Select how many days back to search for invoice emails:
              </p>

              {/* Date Range Options */}
              <div className="space-y-2 mb-6">
                {[
                  { value: 7, label: 'Last 7 days (Recommended)' },
                  { value: 30, label: 'Last 30 days' },
                  { value: 60, label: 'Last 60 days' },
                  { value: 90, label: 'Last 90 days (Maximum)' },
                ].map((option) => (
                  <label
                    key={option.value}
                    className={`flex items-center p-3 border rounded-lg cursor-pointer transition-all ${
                      selectedDays === option.value
                        ? 'border-gray-900 bg-gray-50'
                        : 'border-gray-200 hover:border-gray-400'
                    }`}
                  >
                    <input
                      type="radio"
                      name="days"
                      value={option.value}
                      checked={selectedDays === option.value}
                      onChange={(e) => setSelectedDays(Number(e.target.value))}
                      className="mr-3"
                    />
                    <span className="text-sm text-gray-900">{option.label}</span>
                  </label>
                ))}
              </div>

              {/* Info Text */}
              <div className="bg-blue-50 border border-blue-100 rounded-lg p-3 mb-6">
                <p className="text-xs text-blue-800">
                  <strong>Note:</strong> This will search your Gmail for emails with PDF
                  attachments that match your suppliers or contain invoice keywords. All
                  detected documents will require manual review before becoming invoices.
                </p>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3">
                <button
                  onClick={() => setShowSyncModal(false)}
                  disabled={syncing}
                  className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-200 rounded-lg hover:border-gray-900 transition-colors disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleGmailSync}
                  disabled={syncing}
                  className="flex-1 px-4 py-2 text-sm font-medium text-white bg-gray-900 rounded-lg hover:bg-gray-800 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {syncing ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Syncing...
                    </>
                  ) : (
                    <>
                      <Mail className="w-4 h-4" />
                      Sync
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

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

        @keyframes slide-up {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .animate-slide-down {
          animation: slide-down 0.3s ease-out;
        }

        .animate-slide-up {
          animation: slide-up 0.3s ease-out;
        }
      `}</style>
    </div>
  );
}
