import { useState, useEffect } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  Legend
} from 'recharts';
import './DistributionAnalytics.css';

const API_BASE = 'https://mealmap-api-7vkv.onrender.com';

const COLORS = ['#00b2a9', '#f59e0b', '#8b5cf6', '#ec4899', '#10b981', '#3b82f6'];
const LOCATION_COLORS = {
  DUBLIN: '#00b2a9',
  CORK: '#f59e0b',
  GALWAY: '#8b5cf6'
};

function DistributionAnalytics() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/distribution-stats`);
      if (!res.ok) throw new Error('Failed to fetch stats');
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      setStats(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatKg = (value) => {
    if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
    if (value >= 1000) return `${(value / 1000).toFixed(0)}K`;
    return value.toFixed(0);
  };

  const formatNumber = (value) => {
    return value.toLocaleString();
  };

  if (loading) {
    return (
      <div className="distribution-analytics">
        <div className="analytics-loading">Loading distribution data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="distribution-analytics">
        <div className="analytics-error">Error: {error}</div>
      </div>
    );
  }

  if (!stats) return null;

  const { summary, by_location, by_category, by_source, by_month } = stats;

  // Prepare data for charts
  const locationData = by_location.map(loc => ({
    ...loc,
    kg_out: Math.round(loc.kg_out)
  }));

  const categoryData = by_category.slice(0, 8).map(cat => ({
    name: cat.name.length > 12 ? cat.name.slice(0, 12) + '...' : cat.name,
    fullName: cat.name,
    records: cat.records,
    kg_out: Math.round(cat.kg_out)
  }));

  const sourceData = by_source.filter(s => s.name !== 'Unknown' && s.name !== 'nan').slice(0, 5);

  const monthlyData = by_month.map(m => ({
    month: m.month.slice(5), // Just MM
    kg_in: Math.round(m.kg_in),
    kg_out: Math.round(m.kg_out)
  }));

  return (
    <div className="distribution-analytics">
      <div className="analytics-header">
        <h2>Distribution Analytics</h2>
        <p>Food distribution insights across Ireland</p>
      </div>

      {/* Summary Cards */}
      <div className="summary-cards">
        <div className="summary-card">
          <span className="card-value">{formatNumber(summary.total_records)}</span>
          <span className="card-label">Total Transactions</span>
        </div>
        <div className="summary-card highlight">
          <span className="card-value">{formatKg(summary.total_kg_out)} kg</span>
          <span className="card-label">Food Distributed</span>
        </div>
        <div className="summary-card">
          <span className="card-value">{summary.distribution_rate}%</span>
          <span className="card-label">Distribution Rate</span>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="charts-grid">
        {/* Distribution by Location - Pie Chart */}
        <div className="chart-card">
          <h3>Distribution by Location</h3>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={locationData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={3}
                  dataKey="kg_out"
                  nameKey="name"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  labelLine={false}
                >
                  {locationData.map((entry) => (
                    <Cell key={entry.name} fill={LOCATION_COLORS[entry.name] || COLORS[0]} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value) => [`${formatKg(value)} kg`, 'Distributed']}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Monthly Trend - Area Chart */}
        <div className="chart-card wide">
          <h3>Monthly Distribution Trend</h3>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={monthlyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                <YAxis tickFormatter={formatKg} tick={{ fontSize: 12 }} />
                <Tooltip
                  formatter={(value) => [`${formatKg(value)} kg`]}
                  labelFormatter={(label) => `Month: ${label}`}
                />
                <Area
                  type="monotone"
                  dataKey="kg_out"
                  stroke="#00b2a9"
                  fill="#00b2a9"
                  fillOpacity={0.3}
                  name="Distributed"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top Categories - Bar Chart */}
        <div className="chart-card wide">
          <h3>Top Food Categories</h3>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={categoryData} layout="vertical" margin={{ left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis type="number" tickFormatter={formatKg} tick={{ fontSize: 11 }} />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={90} />
                <Tooltip
                  formatter={(value, name) => [
                    name === 'records' ? formatNumber(value) : `${formatKg(value)} kg`,
                    name === 'records' ? 'Transactions' : 'Distributed'
                  ]}
                  labelFormatter={(_, payload) => payload[0]?.payload?.fullName}
                />
                <Bar dataKey="kg_out" fill="#00b2a9" radius={[0, 4, 4, 0]} name="Distributed" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Sources - Horizontal Bar */}
        <div className="chart-card">
          <h3>Top Sources</h3>
          <div className="source-list">
            {sourceData.map((source, idx) => (
              <div key={source.name} className="source-item">
                <div className="source-info">
                  <span className="source-name">{source.name}</span>
                  <span className="source-count">{formatNumber(source.records)} items</span>
                </div>
                <div className="source-bar-container">
                  <div
                    className="source-bar"
                    style={{
                      width: `${(source.records / sourceData[0].records) * 100}%`,
                      backgroundColor: COLORS[idx % COLORS.length]
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default DistributionAnalytics;
