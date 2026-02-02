export default function DashboardPage() {
  return (
    <div className="p-8">
      {/* Page Title */}
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-gray-900">At a Glance</h1>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        {/* Total Revenue Card */}
        <div className="group relative p-6 bg-white border border-gray-200 rounded-xl hover:border-gray-900 hover:shadow-lg transition-all duration-300">
          <div className="mb-2">
            <p className="text-sm text-gray-600">Total Revenue:</p>
          </div>
          <p className="text-3xl font-semibold text-gray-900">+12,345 EUR</p>
        </div>

        {/* Pending Docs Card */}
        <div className="group relative p-6 bg-white border border-gray-200 rounded-xl hover:border-gray-900 hover:shadow-lg transition-all duration-300">
          <div className="mb-2">
            <p className="text-sm text-gray-600">Pending Docs</p>
          </div>
          <p className="text-3xl font-semibold text-gray-900">12</p>
          <p className="text-xs text-gray-500 mt-2">Needs Action</p>
        </div>

        {/* Active Suppliers Card */}
        <div className="group relative p-6 bg-white border border-gray-200 rounded-xl hover:border-gray-900 hover:shadow-lg transition-all duration-300">
          <div className="mb-2">
            <p className="text-sm text-gray-600">Active Suppliers</p>
          </div>
          <p className="text-3xl font-semibold text-gray-900">45</p>
        </div>
      </div>

      {/* Recent Activity Section */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Invoices</h2>
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <p className="text-gray-500 text-center py-8">
            No invoices yet. Upload or sync documents to get started.
          </p>
        </div>
      </div>
    </div>
  );
}
