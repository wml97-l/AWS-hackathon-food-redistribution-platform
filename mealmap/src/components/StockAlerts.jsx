import { useState, useEffect } from 'react';
import './StockAlerts.css';

const API_BASE =
  import.meta.env.VITE_API_BASE_URL ||
  'https://mealmap-api-7vkv.onrender.com';
  
function StockAlerts() {
  const [stockData, setStockData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [collapsed, setCollapsed] = useState(true);

  useEffect(() => {
    fetchStockLevels();
  }, []);

  const fetchStockLevels = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/stock-alerts`);
      if (!res.ok) throw new Error('Failed to fetch stock alerts');
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      setStockData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatKg = (value) => {
    if (!value && value !== 0) return '-';
    if (value >= 1000) return `${(value / 1000).toFixed(1)}K kg`;
    return `${value.toFixed(1)} kg`;
  };

  const formatRatio = (ratio) => {
    if (!ratio && ratio !== 0) return '-';
    return `${ratio.toFixed(1)}x`;
  };

  if (loading) {
    return (
      <div className="stock-alerts">
        <div className="alerts-loading">Loading stock alerts...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="stock-alerts">
        <div className="alerts-error">
          <span className="error-icon">!</span>
          <span>Stock alerts unavailable: {error}</span>
        </div>
      </div>
    );
  }

  const overstockItems = stockData?.overstock?.overstock_items || [];
  const understockItems = stockData?.understock?.understock_items || [];

  const hasAlerts = overstockItems.length > 0 || understockItems.length > 0;

  if (!hasAlerts) {
    return (
      <div className="stock-alerts">
        <div className="alerts-empty">
          <span className="check-icon">OK</span>
          <span>All stock levels are within normal ranges</span>
        </div>
      </div>
    );
  }

  return (
    <div className="stock-alerts">
      <button className="alerts-header" onClick={() => setCollapsed(!collapsed)} type="button">
        <div className="alerts-title">
          <span className="alert-bell">!</span>
          <h3>Stock Alerts</h3>
          <span className="alert-count">{overstockItems.length + understockItems.length} items need attention</span>
        </div>
        <span className="collapse-icon">
          {collapsed ? '+' : '-'}
        </span>
      </button>

      {!collapsed && (
        <div className="alerts-content">
          {/* Overstock Alerts */}
          {overstockItems.length > 0 && (
            <div className="alert-section overstock">
              <div className="section-header">
                <span className="section-icon overstock">^</span>
                <span className="section-title">Overstock</span>
                <span className="section-subtitle">Items exceeding category average</span>
              </div>
              <div className="alert-cards">
                {overstockItems.map((item, idx) => (
                  <div key={idx} className="alert-card overstock">
                    <div className="card-priority">{idx + 1}</div>
                    <div className="card-content">
                      <div className="card-product">{item.product_name || 'Unknown Product'}</div>
                      <div className="card-category">{item.subcategory || item.category || 'Unknown'}</div>
                    </div>
                    <div className="card-stats">
                      <div className="stat">
                        <span className="stat-value">{formatKg(item.final_stock_kg)}</span>
                        <span className="stat-label">In Stock</span>
                      </div>
                      <div className="stat ratio">
                        <span className="stat-value">{formatRatio(item.ratio_to_category_avg)}</span>
                        <span className="stat-label">vs Avg</span>
                      </div>
                    </div>
                    <div className="card-tooltip">
                      <strong>{item.product_name}</strong>
                      <span>{item.category} &gt; {item.subcategory}</span>
                      <span>{formatKg(item.final_stock_kg)} in stock ({formatRatio(item.ratio_to_category_avg)} category avg)</span>
                      <span className="tooltip-action">Consider pushing to charities or running promotions</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Understock Alerts */}
          {understockItems.length > 0 && (
            <div className="alert-section understock">
              <div className="section-header">
                <span className="section-icon understock">v</span>
                <span className="section-title">Understock</span>
                <span className="section-subtitle">Items running low</span>
              </div>
              <div className="alert-cards">
                {understockItems.map((item, idx) => (
                  <div key={idx} className="alert-card understock">
                    <div className="card-priority">{idx + 1}</div>
                    <div className="card-content">
                      <div className="card-product">{item.product_name || 'Unknown Product'}</div>
                      <div className="card-category">{item.subcategory || item.category || 'Unknown'}</div>
                    </div>
                    <div className="card-stats">
                      <div className="stat">
                        <span className="stat-value">{formatKg(item.final_stock_kg)}</span>
                        <span className="stat-label">In Stock</span>
                      </div>
                      <div className="stat ratio low">
                        <span className="stat-value">{formatRatio(item.ratio_to_category_avg)}</span>
                        <span className="stat-label">vs Avg</span>
                      </div>
                    </div>
                    <div className="card-tooltip">
                      <strong>{item.product_name}</strong>
                      <span>{item.category} &gt; {item.subcategory}</span>
                      <span>{formatKg(item.final_stock_kg)} remaining ({formatRatio(item.ratio_to_category_avg)} category avg)</span>
                      <span className="tooltip-action">Low stock - consider sourcing more donations</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default StockAlerts;
