import { useState, useEffect } from 'react';
import { Users, Plus, Pencil, Trash2, Loader2, X } from 'lucide-react';
import { useWorkspace } from '../../contexts/WorkspaceContext';
import { suppliers } from '../../lib/api';
import type { Supplier } from '../../lib/api/types';

export default function SuppliersPage() {
  const { currentWorkspace } = useWorkspace();
  const [supplierList, setSupplierList] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingSupplier, setEditingSupplier] = useState<Supplier | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    markup_percentage: '',
  });
  const [formLoading, setFormLoading] = useState(false);

  useEffect(() => {
    if (currentWorkspace) {
      fetchSuppliers();
    }
  }, [currentWorkspace]);

  const fetchSuppliers = async () => {
    if (!currentWorkspace) return;

    try {
      setLoading(true);
      setError(null);
      const data = await suppliers.list(currentWorkspace.id);
      setSupplierList(data);
    } catch (err) {
      console.error('Failed to fetch suppliers:', err);
      setError('Failed to load suppliers');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenAdd = () => {
    setFormData({ name: '', email: '', markup_percentage: '' });
    setEditingSupplier(null);
    setShowAddModal(true);
  };

  const handleOpenEdit = (supplier: Supplier) => {
    setFormData({
      name: supplier.name,
      email: supplier.email,
      markup_percentage: supplier.markup_percentage.toString(),
    });
    setEditingSupplier(supplier);
    setShowAddModal(true);
  };

  const handleCloseModal = () => {
    setShowAddModal(false);
    setEditingSupplier(null);
    setFormData({ name: '', email: '', markup_percentage: '' });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentWorkspace) return;

    setFormLoading(true);
    setError(null);

    try {
      if (editingSupplier) {
        // Update existing supplier
        await suppliers.update(editingSupplier.id, {
          name: formData.name,
          email: formData.email,
          markup_percentage: parseFloat(formData.markup_percentage),
        });
      } else {
        // Create new supplier
        await suppliers.create({
          workspace_id: currentWorkspace.id,
          name: formData.name,
          email: formData.email,
          markup_percentage: parseFloat(formData.markup_percentage),
        });
      }

      await fetchSuppliers();
      handleCloseModal();
    } catch (err: any) {
      console.error('Failed to save supplier:', err);
      setError(err.response?.data?.detail || 'Failed to save supplier');
    } finally {
      setFormLoading(false);
    }
  };

  const handleDelete = async (supplier: Supplier) => {
    if (
      !confirm(
        `Delete "${supplier.name}"? This will also delete all associated invoices.`
      )
    )
      return;

    try {
      setError(null);
      const result = await suppliers.delete(supplier.id);
      if (result.deleted_invoices > 0) {
        alert(`Deleted supplier and ${result.deleted_invoices} associated invoices.`);
      }
      await fetchSuppliers();
    } catch (err: any) {
      console.error('Failed to delete supplier:', err);
      setError(err.response?.data?.detail || 'Failed to delete supplier');
    }
  };

  if (!currentWorkspace) {
    return (
      <div className="p-8">
        <div className="text-center py-12 border border-gray-200 rounded-xl bg-white">
          <Users className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">No workspace selected</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      {/* Page Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Suppliers</h1>
          <p className="text-sm text-gray-500 mt-1">
            Manage suppliers and markup percentages
          </p>
        </div>
        <button
          onClick={handleOpenAdd}
          className="flex items-center gap-2 px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors"
        >
          <Plus className="w-4 h-4" />
          Add Supplier
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-100 rounded-xl">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Suppliers Grid */}
      {loading ? (
        <div className="text-center py-12">
          <Loader2 className="w-8 h-8 text-gray-400 animate-spin mx-auto mb-3" />
          <p className="text-gray-500">Loading suppliers...</p>
        </div>
      ) : supplierList.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {supplierList.map((supplier) => (
            <div
              key={supplier.id}
              className="p-4 bg-white border border-gray-200 rounded-xl hover:border-gray-900 hover:shadow-lg transition-all duration-300"
            >
              {/* Supplier Info */}
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-1">
                  {supplier.name}
                </h3>
                <p className="text-sm text-gray-600">{supplier.email}</p>
              </div>

              {/* Markup Badge */}
              <div className="mb-4">
                <span className="inline-flex items-center px-3 py-1 rounded-lg text-sm font-medium bg-green-50 text-green-800 border border-green-200">
                  +{supplier.markup_percentage}% markup
                </span>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-2">
                <button
                  onClick={() => handleOpenEdit(supplier)}
                  className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-200 rounded-lg hover:border-gray-900 transition-colors"
                >
                  <Pencil className="w-4 h-4" />
                  Edit
                </button>
                <button
                  onClick={() => handleDelete(supplier)}
                  className="flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium text-red-700 bg-white border border-red-200 rounded-lg hover:bg-red-50 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12 border border-gray-200 rounded-xl bg-white">
          <Users className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">No suppliers yet</p>
          <p className="text-sm text-gray-400 mt-1">
            Add your first supplier to get started
          </p>
        </div>
      )}

      {/* Add/Edit Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 animate-fade-in">
            {/* Modal Header */}
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-900">
                {editingSupplier ? 'Edit Supplier' : 'Add Supplier'}
              </h2>
              <button
                onClick={handleCloseModal}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Supplier Name
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent"
                  placeholder="e.g., ACME Corp"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email Address
                </label>
                <input
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) =>
                    setFormData({ ...formData, email: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent"
                  placeholder="invoices@acmecorp.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Markup Percentage
                </label>
                <div className="relative">
                  <input
                    type="number"
                    required
                    step="0.01"
                    min="0"
                    max="100"
                    value={formData.markup_percentage}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        markup_percentage: e.target.value,
                      })
                    }
                    className="w-full px-3 py-2 pr-8 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent"
                    placeholder="20"
                  />
                  <span className="absolute right-3 top-2 text-gray-500">%</span>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Invoice total will be increased by this percentage
                </p>
              </div>

              {/* Form Actions */}
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={handleCloseModal}
                  className="flex-1 px-4 py-2 text-gray-700 bg-white border border-gray-200 rounded-lg hover:border-gray-900 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={formLoading}
                  className="flex-1 px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {formLoading ? (
                    <span className="flex items-center justify-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Saving...
                    </span>
                  ) : editingSupplier ? (
                    'Update'
                  ) : (
                    'Add Supplier'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Animation styles */}
      <style>{`
        @keyframes fade-in {
          from {
            opacity: 0;
            transform: scale(0.95);
          }
          to {
            opacity: 1;
            transform: scale(1);
          }
        }

        .animate-fade-in {
          animation: fade-in 0.2s ease-out;
        }
      `}</style>
    </div>
  );
}
