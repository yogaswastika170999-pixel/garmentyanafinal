import { useState, useEffect, useCallback, useRef } from 'react';
import { Search, Clock, Package, Truck, ClipboardCheck, Factory, BarChart3, ShoppingBag, RotateCcw, ChevronDown, ChevronRight, Users } from 'lucide-react';

const STEP_ICONS = {
  'PO Created': Package, 'Vendor Shipment': Truck, 'Material Inspection': ClipboardCheck,
  'Material Request': Package, 'Production Job': Factory, 'Production Progress': BarChart3,
  'Buyer Dispatch': ShoppingBag, 'Production Return': RotateCcw,
};
const STEP_COLORS = {
  'PO Created': 'bg-blue-500', 'Vendor Shipment': 'bg-purple-500', 'Material Inspection': 'bg-emerald-500',
  'Material Request': 'bg-amber-500', 'Production Job': 'bg-indigo-500', 'Production Progress': 'bg-cyan-500',
  'Production Return': 'bg-rose-500',
};
function getStepIcon(step) {
  for (const [key, icon] of Object.entries(STEP_ICONS)) {
    if (step.includes(key)) return icon;
  }
  return Clock;
}
function getStepColor(step) {
  for (const [key, color] of Object.entries(STEP_COLORS)) {
    if (step.includes(key)) return color;
  }
  return 'bg-slate-500';
}

export default function SerialTrackingModule({ token }) {
  const [searchInput, setSearchInput] = useState('');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [expandedIdx, setExpandedIdx] = useState(new Set());
  const debounceRef = useRef(null);

  const fetchTrace = useCallback(async (sn) => {
    if (!sn.trim()) { setData(null); return; }
    setLoading(true);
    try {
      const res = await fetch(`/api/serial-trace?serial=${encodeURIComponent(sn)}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const result = await res.json();
      setData(result);
      setExpandedIdx(new Set());
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, [token]);

  // Auto-search as user types (debounced)
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (searchInput.trim().length >= 2) {
      debounceRef.current = setTimeout(() => fetchTrace(searchInput), 500);
    } else {
      setData(null);
    }
    return () => clearTimeout(debounceRef.current);
  }, [searchInput, fetchTrace]);

  const handleSearch = (e) => { e.preventDefault(); fetchTrace(searchInput); };
  const toggleExpand = (idx) => {
    setExpandedIdx(prev => { const next = new Set(prev); if (next.has(idx)) next.delete(idx); else next.add(idx); return next; });
  };
  const formatDate = (d) => {
    if (!d) return '-';
    try { return new Date(d).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }); }
    catch { return d; }
  };
  const formatNum = (n) => (n || 0).toLocaleString('id-ID');

  const summary = data?.summary || {};
  const allItems = data?.all_items || [];
  const poInfo = data?.po_info || [];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-800">Serial Tracking Timeline</h2>
        <p className="text-slate-500 text-sm mt-1">Lacak siklus lengkap serial number — menampilkan semua item dalam PO</p>
      </div>

      {/* Search */}
      <form onSubmit={handleSearch} className="flex gap-3">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
          <input type="text" value={searchInput} onChange={e => setSearchInput(e.target.value)}
            placeholder="Ketik nomor serial (contoh: SN-001) — otomatis mencari..."
            className="w-full pl-10 pr-4 py-3 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
            data-testid="serial-search-input" />
        </div>
        <button type="submit" disabled={loading || !searchInput.trim()}
          className="px-6 py-3 bg-blue-600 text-white rounded-xl font-medium text-sm hover:bg-blue-700 disabled:opacity-50 transition"
          data-testid="serial-search-btn">
          {loading ? 'Mencari...' : 'Lacak'}
        </button>
      </form>

      {/* Results */}
      {data && (
        <div className="space-y-5">
          {/* Summary Panel */}
          <div className="bg-white rounded-xl border border-slate-200 p-5">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <Clock className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-800">Serial: {data.serial_number}</h3>
                <p className="text-sm text-slate-500">{data.po_count} PO | {data.po_item_count} item ditemukan | {data.timeline.length} event</p>
              </div>
            </div>
            {/* Key metrics */}
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3 mb-4">
              <div className="bg-blue-50 rounded-lg p-3">
                <p className="text-xs text-blue-600 font-medium">Total Order</p>
                <p className="text-lg font-bold text-blue-800">{formatNum(summary.total_ordered)} pcs</p>
              </div>
              <div className="bg-emerald-50 rounded-lg p-3">
                <p className="text-xs text-emerald-600 font-medium">Diproduksi</p>
                <p className="text-lg font-bold text-emerald-800">{formatNum(summary.total_produced)} pcs</p>
              </div>
              <div className="bg-amber-50 rounded-lg p-3">
                <p className="text-xs text-amber-600 font-medium">Belum Diproduksi</p>
                <p className="text-lg font-bold text-amber-800">{formatNum(summary.total_not_produced)} pcs</p>
              </div>
              <div className="bg-purple-50 rounded-lg p-3">
                <p className="text-xs text-purple-600 font-medium">Sudah Dikirim</p>
                <p className="text-lg font-bold text-purple-800">{formatNum(summary.total_shipped)} pcs</p>
              </div>
              <div className="bg-rose-50 rounded-lg p-3">
                <p className="text-xs text-rose-600 font-medium">Belum Dikirim</p>
                <p className="text-lg font-bold text-rose-800">{formatNum(summary.total_not_shipped)} pcs</p>
              </div>
              <div className="bg-slate-50 rounded-lg p-3">
                <p className="text-xs text-slate-600 font-medium">All Serials</p>
                <p className="text-sm font-bold text-slate-800">{(summary.all_serials || []).join(', ') || '-'}</p>
              </div>
            </div>
            {/* Buyer & Vendor info */}
            <div className="flex flex-wrap gap-4 text-sm">
              <div className="flex items-center gap-2">
                <Users className="w-4 h-4 text-slate-400" />
                <span className="text-slate-500">Buyer:</span>
                <span className="font-medium text-slate-800">{summary.buyer || '-'}</span>
              </div>
              <div className="flex items-center gap-2">
                <Factory className="w-4 h-4 text-slate-400" />
                <span className="text-slate-500">Vendor:</span>
                <span className="font-medium text-slate-800">{summary.vendors || '-'}</span>
              </div>
              {poInfo.map((p, i) => (
                <div key={i} className="flex items-center gap-2">
                  <Package className="w-4 h-4 text-slate-400" />
                  <span className="text-slate-500">PO:</span>
                  <span className="font-medium text-slate-800">{p.po_number}</span>
                  <span className={`text-xs px-1.5 py-0.5 rounded ${p.status === 'Closed' ? 'bg-slate-100 text-slate-600' : 'bg-blue-100 text-blue-700'}`}>{p.status}</span>
                </div>
              ))}
            </div>
          </div>

          {/* All Items Table */}
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <div className="px-5 py-3 border-b border-slate-200 bg-slate-50">
              <h4 className="font-semibold text-slate-700 text-sm">Semua Item dalam PO ({allItems.length} items)</h4>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-slate-50 border-b">
                  <tr>
                    <th className="text-left px-4 py-2 font-medium text-slate-600">Serial</th>
                    <th className="text-left px-4 py-2 font-medium text-slate-600">Product</th>
                    <th className="text-left px-4 py-2 font-medium text-slate-600">SKU</th>
                    <th className="text-left px-4 py-2 font-medium text-slate-600">Size</th>
                    <th className="text-left px-4 py-2 font-medium text-slate-600">Color</th>
                    <th className="text-right px-4 py-2 font-medium text-slate-600">Order</th>
                    <th className="text-right px-4 py-2 font-medium text-slate-600">Produced</th>
                    <th className="text-right px-4 py-2 font-medium text-slate-600">Shipped</th>
                    <th className="text-right px-4 py-2 font-medium text-slate-600">Remaining</th>
                  </tr>
                </thead>
                <tbody>
                  {allItems.map((item, idx) => (
                    <tr key={idx} className={`border-b border-slate-50 ${item.is_searched_serial ? 'bg-blue-50' : 'hover:bg-slate-50'}`}>
                      <td className="px-4 py-2 font-medium">
                        {item.serial_number}
                        {item.is_searched_serial && <span className="ml-1 text-xs bg-blue-200 text-blue-700 px-1 rounded">searched</span>}
                      </td>
                      <td className="px-4 py-2">{item.product_name}</td>
                      <td className="px-4 py-2">{item.sku}</td>
                      <td className="px-4 py-2">{item.size}</td>
                      <td className="px-4 py-2">{item.color}</td>
                      <td className="px-4 py-2 text-right font-medium">{item.ordered_qty}</td>
                      <td className="px-4 py-2 text-right text-emerald-600 font-medium">{item.produced_qty}</td>
                      <td className="px-4 py-2 text-right text-purple-600 font-medium">{item.shipped_qty}</td>
                      <td className="px-4 py-2 text-right text-amber-600 font-medium">{item.not_produced}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Timeline */}
          {data.timeline.length > 0 && (
            <div>
              <h4 className="font-semibold text-slate-700 mb-3">Timeline ({data.timeline.length} events)</h4>
              <div className="relative">
                <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-slate-200"></div>
                <div className="space-y-3">
                  {data.timeline.map((event, idx) => {
                    const Icon = getStepIcon(event.step);
                    const color = getStepColor(event.step);
                    const isExpanded = expandedIdx.has(idx);
                    return (
                      <div key={idx} className="relative flex gap-4 pl-2">
                        <div className={`relative z-10 w-9 h-9 ${color} rounded-full flex items-center justify-center flex-shrink-0 shadow-sm`}>
                          <Icon className="w-4 h-4 text-white" />
                        </div>
                        <div className="flex-1 bg-white rounded-xl border border-slate-200 p-3 hover:border-slate-300 transition cursor-pointer"
                             onClick={() => toggleExpand(idx)}>
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <span className="font-medium text-slate-800 text-sm">{event.step}</span>
                              <span className="text-xs text-slate-400">{formatDate(event.date)}</span>
                            </div>
                            {isExpanded ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronRight className="w-4 h-4 text-slate-400" />}
                          </div>
                          <div className="flex flex-wrap gap-1.5 mt-1.5">
                            {event.qty > 0 && <span className="text-xs bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded">Qty: {event.qty}</span>}
                            {event.qty_sent > 0 && <span className="text-xs bg-purple-100 text-purple-600 px-1.5 py-0.5 rounded">Dikirim: {event.qty_sent}</span>}
                            {event.received_qty !== undefined && <span className="text-xs bg-emerald-100 text-emerald-600 px-1.5 py-0.5 rounded">Diterima: {event.received_qty}</span>}
                            {event.missing_qty > 0 && <span className="text-xs bg-red-100 text-red-600 px-1.5 py-0.5 rounded">Missing: {event.missing_qty}</span>}
                            {event.produced_qty !== undefined && event.produced_qty > 0 && <span className="text-xs bg-cyan-100 text-cyan-600 px-1.5 py-0.5 rounded">Produksi: {event.produced_qty}</span>}
                            {event.completed_quantity > 0 && <span className="text-xs bg-blue-100 text-blue-600 px-1.5 py-0.5 rounded">+{event.completed_quantity} pcs</span>}
                            {event.qty_shipped > 0 && <span className="text-xs bg-amber-100 text-amber-600 px-1.5 py-0.5 rounded">Kirim: {event.qty_shipped}</span>}
                            {event.return_qty > 0 && <span className="text-xs bg-rose-100 text-rose-600 px-1.5 py-0.5 rounded">Retur: {event.return_qty}</span>}
                            {event.status && <span className="text-xs bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded">{event.status}</span>}
                            {event.po_number && <span className="text-xs bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded">{event.po_number}</span>}
                            {event.shipment_number && <span className="text-xs bg-purple-50 text-purple-600 px-1.5 py-0.5 rounded">{event.shipment_number}</span>}
                            {event.job_number && <span className="text-xs bg-indigo-50 text-indigo-600 px-1.5 py-0.5 rounded">{event.job_number}</span>}
                          </div>
                          {isExpanded && (
                            <div className="mt-2 pt-2 border-t border-slate-100 grid grid-cols-2 gap-1.5">
                              {Object.entries(event).filter(([k]) => !['step', 'date', 'module'].includes(k)).map(([k, v]) => (
                                v !== null && v !== undefined && v !== '' && (
                                  <div key={k} className="text-xs">
                                    <span className="text-slate-400">{k.replace(/_/g, ' ')}:</span>{' '}
                                    <span className="text-slate-700 font-medium">{String(v)}</span>
                                  </div>
                                )
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Empty state */}
      {!data && !loading && (
        <div className="text-center py-16">
          <Search className="w-16 h-16 text-slate-200 mx-auto mb-4" />
          <p className="text-slate-400 text-lg">Masukkan nomor serial untuk melacak</p>
          <p className="text-slate-300 text-sm mt-1">Otomatis mencari saat mengetik (min. 2 karakter)</p>
        </div>
      )}
    </div>
  );
}
