import { useState, useEffect } from 'react';
import { Receipt, Download, Loader2, ArrowUpDown, FileText, X } from 'lucide-react';
import { useWorkspace } from '../../contexts/WorkspaceContext';
import { invoices, workspaces } from '../../lib/api';
import type { Invoice } from '../../lib/api/types';

export default function InvoicesPage() {
  const { currentWorkspace } = useWorkspace();
  const [invoiceList, setInvoiceList] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Consolidated Invoice Modal State
  const [showModal, setShowModal] = useState(false);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [preview, setPreview] = useState<any>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [generatingPdf, setGeneratingPdf] = useState(false);
  const [modalError, setModalError] = useState<string | null>(null);

  useEffect(() => {
    if (currentWorkspace) {
      fetchInvoices();
    }
  }, [currentWorkspace, sortOrder]);

  const fetchInvoices = async () => {
    if (!currentWorkspace) return;

    try {
      setLoading(true);
      setError(null);
      const data = await invoices.list(currentWorkspace.id, sortOrder);
      setInvoiceList(data);
    } catch (err) {
      console.error('Failed to fetch invoices:', err);
      setError('Failed to load invoices');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (invoice: Invoice) => {
    try {
      const blobUrl = await invoices.downloadPdf(invoice.id);

      // Create temporary link and trigger download
      const a = document.createElement('a');
      a.href = blobUrl;
      a.download = `invoice-${invoice.id}-${invoice.supplier?.name || 'unknown'}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);

      // Clean up blob URL
      URL.revokeObjectURL(blobUrl);
    } catch (err) {
      console.error('Download failed:', err);
      setError('Failed to download invoice');
    }
  };

  const toggleSort = () => {
    setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc');
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'EUR',
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  // Consolidated Invoice Functions
  const openModal = () => {
    setShowModal(true);
    setModalError(null);
    setPreview(null);
    // Set default dates: current month
    const now = new Date();
    const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
    const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0);
    setStartDate(firstDay.toISOString().split('T')[0]);
    setEndDate(lastDay.toISOString().split('T')[0]);
  };

  const closeModal = () => {
    setShowModal(false);
    setModalError(null);
    setPreview(null);
  };

  const handlePreview = async () => {
    if (!currentWorkspace || !startDate || !endDate) return;

    try {
      setLoadingPreview(true);
      setModalError(null);
      const previewData = await workspaces.previewConsolidatedInvoice(
        currentWorkspace.id,
        startDate,
        endDate
      );
      setPreview(previewData);
    } catch (err: any) {
      console.error('Preview failed:', err);
      setModalError(err.response?.data?.detail || 'Failed to load preview');
      setPreview(null);
    } finally {
      setLoadingPreview(false);
    }
  };

  const handleGenerate = async () => {
    if (!currentWorkspace || !startDate || !endDate) return;

    try {
      setGeneratingPdf(true);
      setModalError(null);
      const blob = await workspaces.generateConsolidatedInvoice(
        currentWorkspace.id,
        startDate,
        endDate
      );

      // Create download link
      const blobUrl = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = blobUrl;
      a.download = `consolidated_invoice_${startDate}_${endDate}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(blobUrl);

      // Close modal on success
      closeModal();
    } catch (err: any) {
      console.error('Generate failed:', err);
      setModalError(err.response?.data?.detail || 'Failed to generate invoice');
    } finally {
      setGeneratingPdf(false);
    }
  };

  // Calculate totals
  const totalOriginal = invoiceList.reduce((sum, inv) => sum + inv.original_total, 0);
  const totalWithMarkup = invoiceList.reduce((sum, inv) => sum + inv.markup_total, 0);

  if (!currentWorkspace) {
    return (
      <div className="p-8">
        <div className="text-center py-12 border border-gray-200 rounded-xl bg-white">
          <Receipt className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">No workspace selected</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      {/* Page Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">Invoices</h1>
            <p className="text-sm text-gray-500 mt-1">
              View and download processed invoices
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={openModal}
              disabled={invoiceList.length === 0}
              className="flex items-center gap-2 px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <FileText className="w-4 h-4" />
              Generate Consolidated Invoice
            </button>
            <button
              onClick={toggleSort}
              className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg hover:border-gray-900 transition-colors"
            >
              <ArrowUpDown className="w-4 h-4" />
              {sortOrder === 'desc' ? 'Newest First' : 'Oldest First'}
            </button>
          </div>
        </div>

        {/* Summary Cards */}
        {invoiceList.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="p-4 bg-white border border-gray-200 rounded-xl">
              <p className="text-sm text-gray-600 mb-1">Total Invoices</p>
              <p className="text-2xl font-semibold text-gray-900">
                {invoiceList.length}
              </p>
            </div>
            <div className="p-4 bg-white border border-gray-200 rounded-xl">
              <p className="text-sm text-gray-600 mb-1">Original Total</p>
              <p className="text-2xl font-semibold text-gray-900">
                {formatCurrency(totalOriginal)}
              </p>
            </div>
            <div className="p-4 bg-white border border-gray-200 rounded-xl">
              <p className="text-sm text-gray-600 mb-1">Total with Markup</p>
              <p className="text-2xl font-semibold text-green-700">
                {formatCurrency(totalWithMarkup)}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-100 rounded-xl">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Invoices Table */}
      {loading ? (
        <div className="text-center py-12">
          <Loader2 className="w-8 h-8 text-gray-400 animate-spin mx-auto mb-3" />
          <p className="text-gray-500">Loading invoices...</p>
        </div>
      ) : invoiceList.length > 0 ? (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                    Supplier
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase tracking-wider">
                    Invoice Date
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-600 uppercase tracking-wider">
                    Original Total
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-600 uppercase tracking-wider">
                    Markup
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-600 uppercase tracking-wider">
                    Total + Markup
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-600 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {invoiceList.map((invoice) => {
                  const markupAmount = invoice.markup_total - invoice.original_total;
                  const markupPercentage = invoice.supplier?.markup_percentage || 0;

                  return (
                    <tr
                      key={invoice.id}
                      className="hover:bg-gray-50 transition-colors"
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {invoice.supplier?.name || 'Unknown Supplier'}
                        </div>
                        <div className="text-xs text-gray-500">
                          {invoice.supplier?.email}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {formatDate(invoice.invoice_date)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                        {formatCurrency(invoice.original_total)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-50 text-green-800">
                          +{markupPercentage}% ({formatCurrency(markupAmount)})
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-semibold text-gray-900">
                        {formatCurrency(invoice.markup_total)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <button
                          onClick={() => handleDownload(invoice)}
                          className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-200 rounded-lg hover:border-gray-900 transition-colors"
                        >
                          <Download className="w-3.5 h-3.5" />
                          Download
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="text-center py-12 border border-gray-200 rounded-xl bg-white">
          <Receipt className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">No invoices yet</p>
          <p className="text-sm text-gray-400 mt-1">
            Process documents to create invoices
          </p>
        </div>
      )}

      {/* Consolidated Invoice Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">
                Generate Consolidated Invoice
              </h2>
              <button
                onClick={closeModal}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 space-y-6">
              {/* Date Range Selection */}
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Start Date
                  </label>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    End Date
                  </label>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent"
                  />
                </div>
              </div>

              {/* Preview Button */}
              <button
                onClick={handlePreview}
                disabled={!startDate || !endDate || loadingPreview}
                className="w-full px-4 py-2 bg-gray-100 text-gray-900 rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {loadingPreview ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Loading Preview...
                  </>
                ) : (
                  'Show Preview'
                )}
              </button>

              {/* Error Message */}
              {modalError && (
                <div className="p-4 bg-red-50 border border-red-100 rounded-lg">
                  <p className="text-sm text-red-800">{modalError}</p>
                </div>
              )}

              {/* Preview Results */}
              {preview && (
                <div className="space-y-3 p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <h3 className="font-medium text-gray-900 mb-3">
                    Invoice Preview
                  </h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Number of Invoices:</span>
                      <span className="font-medium text-gray-900">
                        {preview.invoice_count}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Original Total:</span>
                      <span className="font-medium text-gray-900">
                        {formatCurrency(preview.total_original)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Markup Earned:</span>
                      <span className="font-medium text-green-700">
                        +{formatCurrency(preview.total_markup)}
                      </span>
                    </div>
                    <div className="flex justify-between pt-2 mt-2 border-t border-gray-300">
                      <span className="font-semibold text-gray-900">Total to Bill:</span>
                      <span className="font-semibold text-gray-900 text-lg">
                        {formatCurrency(preview.total_billed)}
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200">
              <button
                onClick={closeModal}
                className="px-4 py-2 text-gray-700 hover:text-gray-900 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleGenerate}
                disabled={!preview || generatingPdf}
                className="px-6 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {generatingPdf ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4" />
                    Generate & Download
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
