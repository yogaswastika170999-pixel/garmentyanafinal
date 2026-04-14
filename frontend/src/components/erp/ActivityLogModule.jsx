
import { useState, useEffect } from 'react';
import { RefreshCw, Filter, Activity } from 'lucide-react';

const ACTION_COLORS = {
  Create: 'bg-emerald-100 text-emerald-700',
  Update: 'bg-blue-100 text-blue-700',
  Delete: 'bg-red-100 text-red-700',
  Login: 'bg-purple-100 text-purple-700',
  'Auto Generate': 'bg-amber-100 text-amber-700',
};

const MODULE_ICONS = {
  'Production PO': '📋',
  'Work Order': '🏭',
  'Production Progress': '📈',
  'Garments': '👔',
  'Products': '📦',
  'Invoice': '🧾',
  'Payment': '💰',
  'User Management': '👤',
  'Auth': '🔐',
};

export default function ActivityLogModule({ token }) {
  const [logs, setLogs] = useState([]);
  const [users, setUsers] = useState([]);  // NEW: user list for filter
  const [loading, setLoading] = useState(true);
  const [filterModule, setFilterModule] = useState('');
  const [filterUser, setFilterUser] = useState('');  // NEW: user filter

  const modules = [...new Set(logs.map(l => l.module))];

  useEffect(() => { fetchLogs(); fetchUsers(); }, []);

  const fetchLogs = async () => {
    setLoading(true);
    const params = new URLSearchParams({ limit: '200' });
    if (filterModule) params.append('module', filterModule);
    if (filterUser) params.append('user_id', filterUser);
    const url = `/api/activity-logs?${params}`;
    const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
    const data = await res.json();
    setLogs(Array.isArray(data) ? data : []);
    setLoading(false);
  };

  const fetchUsers = async () => {
    const res = await fetch('/api/users', { headers: { Authorization: `Bearer ${token}` } });
    const data = await res.json();
    setUsers(Array.isArray(data) ? data : []);
  };

  const filtered = logs;  // Filtering already done server-side

  const formatDateTime = (d) => {
    if (!d) return '-';
    return new Date(d).toLocaleString('id-ID', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Log Aktivitas</h1>
          <p className="text-slate-500 text-sm mt-1">Rekam jejak semua aktivitas sistem</p>
        </div>
        <button onClick={fetchLogs} className="flex items-center gap-2 px-3 py-2 border border-slate-200 rounded-lg text-sm hover:bg-slate-50">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Filter */}
      <div className="flex flex-wrap gap-2 items-center">
        <Filter className="w-4 h-4 text-slate-500" />
        <button onClick={() => setFilterModule('')}
          className={`px-3 py-1.5 rounded-lg text-sm border transition-colors ${!filterModule ? 'bg-blue-600 text-white border-blue-600' : 'border-slate-200 text-slate-600 hover:bg-slate-50'}`}>
          Semua Modul
        </button>
        {modules.map(m => (
          <button key={m} onClick={() => setFilterModule(m)}
            className={`px-3 py-1.5 rounded-lg text-sm border transition-colors ${
              filterModule === m ? 'bg-blue-600 text-white border-blue-600' : 'border-slate-200 text-slate-600 hover:bg-slate-50'
            }`}>
            {MODULE_ICONS[m] || '📌'} {m}
          </button>
        ))}
      </div>

      {/* User Filter */}
      <div className="bg-white p-3 rounded-lg border border-slate-200">
        <div className="flex items-center gap-3">
          <label className="text-sm font-medium text-slate-700 whitespace-nowrap">Filter User:</label>
          <select value={filterUser} onChange={(e) => { setFilterUser(e.target.value); }}
            className="flex-1 px-3 py-2 border border-slate-300 rounded-lg text-sm">
            <option value="">Semua User</option>
            {users.map(u => <option key={u.id} value={u.id}>{u.name} - {u.email}</option>)}
          </select>
          <button onClick={fetchLogs} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 whitespace-nowrap">
            Terapkan Filter
          </button>
        </div>
      </div>


      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { action: 'Create', label: 'Dibuat', color: 'border-l-emerald-500' },
          { action: 'Update', label: 'Diubah', color: 'border-l-blue-500' },
          { action: 'Delete', label: 'Dihapus', color: 'border-l-red-500' },
          { action: 'Login', label: 'Login', color: 'border-l-purple-500' },
        ].map(s => (
          <div key={s.action} className={`bg-white rounded-xl border border-slate-200 border-l-4 ${s.color} p-4 shadow-sm`}>
            <p className="text-xs text-slate-500">{s.label}</p>
            <p className="text-2xl font-bold text-slate-800 mt-1">
              {logs.filter(l => l.action === s.action).length}
            </p>
          </div>
        ))}
      </div>

      {/* Log List */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm">
        <div className="px-5 py-4 border-b border-slate-100">
          <h3 className="font-semibold text-slate-700">
            <Activity className="w-4 h-4 inline mr-2 text-blue-500" />
            Aktivitas Terbaru ({filtered.length})
          </h3>
        </div>
        <div className="divide-y divide-slate-100 max-h-[600px] overflow-y-auto">
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : filtered.length === 0 ? (
            <div className="text-center py-16 text-slate-400">Belum ada aktivitas</div>
          ) : (
            filtered.map(log => (
              <div key={log.id} className="flex items-start gap-4 px-5 py-4 hover:bg-slate-50">
                <div className="w-9 h-9 rounded-full bg-blue-100 flex items-center justify-center text-sm flex-shrink-0">
                  {MODULE_ICONS[log.module] || <Activity className="w-4 h-4 text-blue-500" />}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-medium text-sm text-slate-800">{log.user_name}</span>
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${ACTION_COLORS[log.action] || 'bg-slate-100 text-slate-600'}`}>
                      {log.action}
                    </span>
                    <span className="text-xs text-slate-500 bg-slate-100 px-2 py-0.5 rounded">{log.module}</span>
                  </div>
                  <p className="text-sm text-slate-600 mt-0.5">{log.details}</p>
                </div>
                <div className="text-xs text-slate-400 whitespace-nowrap flex-shrink-0">
                  {formatDateTime(log.timestamp)}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
