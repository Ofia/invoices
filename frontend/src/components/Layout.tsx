import { ReactNode, useState, useEffect, useRef } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Folder,
  Users,
  FileText,
  Receipt,
  LogOut,
  Search,
  Loader2
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useWorkspace } from '../contexts/WorkspaceContext';
import { search } from '../lib/api';
import type { SearchResponse } from '../lib/api/types';

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const { user, logout } = useAuth();
  const { currentWorkspace } = useWorkspace();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResponse | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);
  const searchTimeoutRef = useRef<NodeJS.Timeout>();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // Close search results when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setShowResults(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Debounced search
  useEffect(() => {
    if (searchQuery.length < 2) {
      setSearchResults(null);
      setShowResults(false);
      return;
    }

    if (!currentWorkspace) return;

    // Clear previous timeout
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    // Set new timeout
    searchTimeoutRef.current = setTimeout(async () => {
      try {
        setIsSearching(true);
        console.log('Searching for:', searchQuery, 'in workspace:', currentWorkspace.id);
        const results = await search.query(searchQuery, currentWorkspace.id);
        console.log('Search results:', results);
        setSearchResults(results);
        setShowResults(true);
      } catch (err) {
        console.error('Search failed:', err);
        console.error('Error details:', err);
        setSearchResults(null);
      } finally {
        setIsSearching(false);
      }
    }, 300);

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [searchQuery, currentWorkspace]);

  const handleResultClick = (type: 'invoice' | 'supplier' | 'document', id: number) => {
    setShowResults(false);
    setSearchQuery('');
    setSearchResults(null);

    // Navigate to appropriate page
    if (type === 'invoice') {
      navigate('/invoices', { state: { highlightId: id } });
    } else if (type === 'supplier') {
      navigate('/suppliers', { state: { highlightId: id } });
    } else if (type === 'document') {
      navigate('/documents', { state: { highlightId: id } });
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 2,
    }).format(amount);
  };

  const navItems = [
    { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/documents', icon: FileText, label: 'Documents' },
    { path: '/invoices', icon: Receipt, label: 'Invoices' },
    { path: '/suppliers', icon: Users, label: 'Suppliers' },
  ];

  return (
    <div className="flex min-h-screen bg-white">
      {/* Sidebar */}
      <aside className="w-64 border-r border-gray-200 flex flex-col">
        {/* Logo/Brand */}
        <div className="h-16 flex items-center px-6 border-b border-gray-200">
          <h1 className="text-lg font-semibold text-gray-900">Invoice Manager</h1>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors
                  ${
                    isActive
                      ? 'bg-gray-100 text-gray-900'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }`
                }
              >
                <Icon className="w-5 h-5" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* User Section */}
        <div className="p-3 border-t border-gray-200">
          <div className="px-3 py-2 mb-2">
            <p className="text-xs text-gray-500 mb-1">Signed in as</p>
            <p className="text-sm font-medium text-gray-900 truncate">{user?.email}</p>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-50 hover:text-gray-900 transition-colors w-full"
          >
            <LogOut className="w-5 h-5" />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col">
        {/* Top Bar */}
        <header className="h-16 border-b border-gray-200 flex items-center justify-between px-8">
          <div className="text-sm text-gray-600">
            Workspace / Overview
          </div>
          <div className="flex items-center gap-4">
            {/* Global Search */}
            <div className="relative" ref={searchRef}>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search invoices, suppliers..."
                  className="w-64 h-9 border border-gray-200 rounded-lg pl-9 pr-9 text-sm focus:outline-none focus:border-gray-900 transition-colors"
                  disabled={!currentWorkspace}
                />
                {isSearching && (
                  <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 animate-spin" />
                )}
              </div>

              {/* Search Results Dropdown */}
              {showResults && searchResults && searchResults.total_results > 0 && (
                <div className="absolute top-full mt-2 w-96 bg-white border border-gray-200 rounded-lg shadow-xl z-50 max-h-96 overflow-y-auto">
                  {/* Invoices */}
                  {searchResults.invoices.length > 0 && (
                    <div className="p-2">
                      <div className="px-2 py-1 text-xs font-semibold text-gray-500 uppercase">
                        Invoices ({searchResults.invoices.length})
                      </div>
                      {searchResults.invoices.map((invoice) => (
                        <button
                          key={`invoice-${invoice.id}`}
                          onClick={() => handleResultClick('invoice', invoice.id)}
                          className="w-full text-left px-3 py-2 rounded-lg hover:bg-gray-50 transition-colors"
                        >
                          <div className="flex items-center gap-2">
                            <Receipt className="w-4 h-4 text-gray-400 flex-shrink-0" />
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-gray-900 truncate">
                                {invoice.supplier_name}
                              </p>
                              <p className="text-xs text-gray-500">
                                {new Date(invoice.invoice_date).toLocaleDateString()} •{' '}
                                {formatCurrency(invoice.markup_total)}
                              </p>
                            </div>
                          </div>
                        </button>
                      ))}
                    </div>
                  )}

                  {/* Suppliers */}
                  {searchResults.suppliers.length > 0 && (
                    <div className="p-2 border-t border-gray-100">
                      <div className="px-2 py-1 text-xs font-semibold text-gray-500 uppercase">
                        Suppliers ({searchResults.suppliers.length})
                      </div>
                      {searchResults.suppliers.map((supplier) => (
                        <button
                          key={`supplier-${supplier.id}`}
                          onClick={() => handleResultClick('supplier', supplier.id)}
                          className="w-full text-left px-3 py-2 rounded-lg hover:bg-gray-50 transition-colors"
                        >
                          <div className="flex items-center gap-2">
                            <Users className="w-4 h-4 text-gray-400 flex-shrink-0" />
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-gray-900 truncate">
                                {supplier.name}
                              </p>
                              <p className="text-xs text-gray-500 truncate">
                                {supplier.email}
                              </p>
                            </div>
                          </div>
                        </button>
                      ))}
                    </div>
                  )}

                  {/* Documents */}
                  {searchResults.documents.length > 0 && (
                    <div className="p-2 border-t border-gray-100">
                      <div className="px-2 py-1 text-xs font-semibold text-gray-500 uppercase">
                        Documents ({searchResults.documents.length})
                      </div>
                      {searchResults.documents.map((doc) => (
                        <button
                          key={`doc-${doc.id}`}
                          onClick={() => handleResultClick('document', doc.id)}
                          className="w-full text-left px-3 py-2 rounded-lg hover:bg-gray-50 transition-colors"
                        >
                          <div className="flex items-center gap-2">
                            <FileText className="w-4 h-4 text-gray-400 flex-shrink-0" />
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-gray-900 truncate">
                                {doc.filename}
                              </p>
                              <p className="text-xs text-gray-500">
                                {doc.status} • {new Date(doc.uploaded_at).toLocaleDateString()}
                              </p>
                            </div>
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* No Results */}
              {showResults && searchResults && searchResults.total_results === 0 && (
                <div className="absolute top-full mt-2 w-96 bg-white border border-gray-200 rounded-lg shadow-xl z-50 p-4">
                  <p className="text-sm text-gray-500 text-center">
                    No results found for "{searchResults.query}"
                  </p>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Page Content */}
        <div className="flex-1 overflow-auto">
          {children}
        </div>
      </main>
    </div>
  );
}
