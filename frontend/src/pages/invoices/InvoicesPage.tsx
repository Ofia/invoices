import { useState, useEffect } from 'react';
import { Receipt, Download, Loader2, ArrowUpDown } from 'lucide-react';
import { useWorkspace } from '../../contexts/WorkspaceContext';
import { invoices } from '../../lib/api';
import type { Invoice } from '../../lib/api/types';

export default function InvoicesPage() {
  const { currentWorkspace } = useWorkspace();
  const [invoiceList, setInvoiceList] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

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
          <button
            onClick={toggleSort}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg hover:border-gray-900 transition-colors"
          >
            <ArrowUpDown className="w-4 h-4" />
            {sortOrder === 'desc' ? 'Newest First' : 'Oldest First'}
          </button>
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
    </div>
  );
}
