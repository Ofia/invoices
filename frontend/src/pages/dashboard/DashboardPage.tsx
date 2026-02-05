import { useState, useEffect } from 'react';
import { Loader2, FileText, Download, ChevronDown } from 'lucide-react';
import { useWorkspace } from '../../contexts/WorkspaceContext';
import { invoices, documents, suppliers } from '../../lib/api';
import type { Invoice, PendingDocument, Supplier } from '../../lib/api/types';

type Currency = 'EUR' | 'USD' | 'GBP';

interface ExchangeRates {
  EUR: number;
  USD: number;
  GBP: number;
}

export default function DashboardPage() {
  const { currentWorkspace } = useWorkspace();
  const [loading, setLoading] = useState(true);
  const [totalRevenue, setTotalRevenue] = useState(0);
  const [totalMarkup, setTotalMarkup] = useState(0);
  const [pendingDocsCount, setPendingDocsCount] = useState(0);
  const [activeSuppliersCount, setActiveSuppliersCount] = useState(0);
  const [recentInvoices, setRecentInvoices] = useState<Invoice[]>([]);
  const [currency, setCurrency] = useState<Currency>(() => {
    return (localStorage.getItem('preferredCurrency') as Currency) || 'EUR';
  });
  const [exchangeRates, setExchangeRates] = useState<ExchangeRates>({
    EUR: 1,
    USD: 1,
    GBP: 1,
  });
  const [showCurrencyDropdown, setShowCurrencyDropdown] = useState(false);

  useEffect(() => {
    if (currentWorkspace) {
      fetchDashboardData();
    }
  }, [currentWorkspace]);

  useEffect(() => {
    fetchExchangeRates();
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = () => {
      if (showCurrencyDropdown) {
        setShowCurrencyDropdown(false);
      }
    };

    if (showCurrencyDropdown) {
      document.addEventListener('click', handleClickOutside);
    }

    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  }, [showCurrencyDropdown]);

  const fetchExchangeRates = async () => {
    try {
      // Frankfurter API - Free, no API key needed
      const response = await fetch('https://api.frankfurter.app/latest?from=EUR&to=USD,GBP');
      const data = await response.json();

      setExchangeRates({
        EUR: 1, // Base currency
        USD: data.rates.USD,
        GBP: data.rates.GBP,
      });
    } catch (err) {
      console.error('Failed to fetch exchange rates:', err);
      // Keep default rates of 1:1 if fetch fails
    }
  };

  const handleCurrencyChange = (newCurrency: Currency) => {
    setCurrency(newCurrency);
    localStorage.setItem('preferredCurrency', newCurrency);
    setShowCurrencyDropdown(false);
  };

  const convertAmount = (amountInEUR: number): number => {
    return amountInEUR * exchangeRates[currency];
  };

  const fetchDashboardData = async () => {
    if (!currentWorkspace) return;

    try {
      setLoading(true);

      // Fetch all data in parallel
      const [invoicesList, documentsList, suppliersList] = await Promise.all([
        invoices.list(currentWorkspace.id, 'desc'),
        documents.list(currentWorkspace.id),
        suppliers.list(currentWorkspace.id),
      ]);

      // Calculate total revenue from markup totals
      const revenue = invoicesList.reduce((sum, inv) => sum + inv.markup_total, 0);
      setTotalRevenue(revenue);

      // Calculate total markup (difference between markup and original)
      const markup = invoicesList.reduce(
        (sum, inv) => sum + (inv.markup_total - inv.original_total),
        0
      );
      setTotalMarkup(markup);

      // Count pending documents
      const pendingCount = documentsList.filter((doc) => doc.status === 'pending').length;
      setPendingDocsCount(pendingCount);

      // Count active suppliers
      setActiveSuppliersCount(suppliersList.length);

      // Get 5 most recent invoices
      setRecentInvoices(invoicesList.slice(0, 5));
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (invoice: Invoice) => {
    try {
      const pdfUrl = await invoices.downloadPdf(invoice.id);
      const link = document.createElement('a');
      link.href = pdfUrl;
      link.download = `invoice-${invoice.id}.pdf`;
      link.click();
      URL.revokeObjectURL(pdfUrl);
    } catch (err) {
      console.error('Failed to download invoice:', err);
      alert('Failed to download invoice');
    }
  };

  const formatCurrency = (amountInEUR: number) => {
    const convertedAmount = convertAmount(amountInEUR);
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 2,
    }).format(convertedAmount);
  };

  if (!currentWorkspace) {
    return (
      <div className="p-8">
        <div className="text-center py-12 border border-gray-200 rounded-xl bg-white">
          <p className="text-gray-500">No workspace selected</p>
          <p className="text-sm text-gray-400 mt-1">
            Please create or select a workspace first
          </p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="p-8">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 text-gray-400 animate-spin" />
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      {/* Page Title with Currency Selector */}
      <div className="mb-8 flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-gray-900">At a Glance</h1>

        {/* Currency Selector */}
        <div className="relative">
          <button
            onClick={(e) => {
              e.stopPropagation();
              setShowCurrencyDropdown(!showCurrencyDropdown);
            }}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-200 rounded-lg hover:border-gray-900 transition-colors"
          >
            <span>{currency}</span>
            <ChevronDown className="w-4 h-4" />
          </button>

          {/* Dropdown Menu */}
          {showCurrencyDropdown && (
            <div className="absolute right-0 mt-2 w-32 bg-white border border-gray-200 rounded-lg shadow-lg z-10">
              {(['EUR', 'USD', 'GBP'] as Currency[]).map((curr) => (
                <button
                  key={curr}
                  onClick={() => handleCurrencyChange(curr)}
                  className={`w-full px-4 py-2 text-left text-sm hover:bg-gray-50 transition-colors first:rounded-t-lg last:rounded-b-lg ${
                    curr === currency ? 'bg-gray-100 font-medium' : ''
                  }`}
                >
                  {curr}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
        {/* Total Revenue Card */}
        <div className="group relative p-6 bg-white border border-gray-200 rounded-xl hover:border-gray-900 hover:shadow-lg transition-all duration-300">
          <div className="mb-2">
            <p className="text-sm text-gray-600">Total Revenue:</p>
          </div>
          <p className="text-3xl font-semibold text-gray-900">
            {formatCurrency(totalRevenue)}
          </p>
        </div>

        {/* Total Markup Card */}
        <div className="group relative p-6 bg-white border border-gray-200 rounded-xl hover:border-gray-900 hover:shadow-lg transition-all duration-300">
          <div className="mb-2">
            <p className="text-sm text-gray-600">Total Markup:</p>
          </div>
          <p className="text-3xl font-semibold text-green-600">
            +{formatCurrency(totalMarkup)}
          </p>
        </div>

        {/* Pending Docs Card */}
        <div className="group relative p-6 bg-white border border-gray-200 rounded-xl hover:border-gray-900 hover:shadow-lg transition-all duration-300">
          <div className="mb-2">
            <p className="text-sm text-gray-600">Pending Docs</p>
          </div>
          <p className="text-3xl font-semibold text-gray-900">{pendingDocsCount}</p>
          <p className="text-xs text-gray-500 mt-2">Needs Action</p>
        </div>

        {/* Active Suppliers Card */}
        <div className="group relative p-6 bg-white border border-gray-200 rounded-xl hover:border-gray-900 hover:shadow-lg transition-all duration-300">
          <div className="mb-2">
            <p className="text-sm text-gray-600">Active Suppliers</p>
          </div>
          <p className="text-3xl font-semibold text-gray-900">{activeSuppliersCount}</p>
        </div>
      </div>

      {/* Recent Activity Section */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Invoices</h2>
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          {recentInvoices.length > 0 ? (
            <div className="divide-y divide-gray-200">
              {recentInvoices.map((invoice) => (
                <div
                  key={invoice.id}
                  className="p-4 hover:bg-gray-50 transition-colors flex items-center justify-between"
                >
                  <div className="flex items-center gap-4 flex-1">
                    <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center flex-shrink-0">
                      <FileText className="w-5 h-5 text-gray-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900">
                        {invoice.supplier?.name || 'Unknown Supplier'}
                      </p>
                      <p className="text-xs text-gray-500 mt-0.5">
                        {new Date(invoice.invoice_date).toLocaleDateString()} •{' '}
                        {formatCurrency(invoice.original_total)} →{' '}
                        {formatCurrency(invoice.markup_total)}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => handleDownload(invoice)}
                    className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                    title="Download PDF"
                  >
                    <Download className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-6">
              <p className="text-gray-500 text-center py-8">
                No invoices yet. Upload or sync documents to get started.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
