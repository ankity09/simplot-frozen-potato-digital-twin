import React, { useState, useEffect } from 'react';
import './Dashboard.css';

const Dashboard = ({ telemetryData, graphData }) => {
  const [refreshInterval, setRefreshInterval] = useState(30);
  const [timeRange, setTimeRange] = useState('1h');

  // Calculate statistics from telemetry data
  const calculateStats = () => {
    if (!telemetryData || telemetryData.length === 0) {
      return {
        avgTemp: 0,
        maxTemp: 0,
        minTemp: 0,
        totalAlerts: 0,
        activeComponents: 0,
      };
    }

    const temps = telemetryData.map(t => t.sensorAReading || 0);
    return {
      avgTemp: (temps.reduce((a, b) => a + b, 0) / temps.length).toFixed(2),
      maxTemp: Math.max(...temps).toFixed(2),
      minTemp: Math.min(...temps).toFixed(2),
      totalAlerts: telemetryData.filter(t => (t.sensorAReading || 0) > 100).length,
      activeComponents: telemetryData.length,
    };
  };

  const stats = calculateStats();

  // Get production line metrics
  const getLineMetrics = () => {
    const lines = {
      'French Fries': { components: 6, healthy: 0, warnings: 0, critical: 0 },
      'Hash Browns': { components: 5, healthy: 0, warnings: 0, critical: 0 },
      'Wedges': { components: 5, healthy: 0, warnings: 0, critical: 0 },
    };

    telemetryData.forEach(item => {
      const id = item.component_id || '';
      let line = null;

      if (id.startsWith('FF-')) line = 'French Fries';
      else if (id.startsWith('HB-')) line = 'Hash Browns';
      else if (id.startsWith('WG-')) line = 'Wedges';

      if (line && lines[line]) {
        const reading = item.sensorAReading || 0;
        if (reading > 180) lines[line].critical++;
        else if (reading > 150) lines[line].warnings++;
        else lines[line].healthy++;
      }
    });

    return lines;
  };

  const lineMetrics = getLineMetrics();

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h2>📈 Production Dashboard</h2>
        <div className="dashboard-controls">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="dashboard-select"
          >
            <option value="15m">Last 15 minutes</option>
            <option value="1h">Last hour</option>
            <option value="4h">Last 4 hours</option>
            <option value="24h">Last 24 hours</option>
          </select>
          <select
            value={refreshInterval}
            onChange={(e) => setRefreshInterval(parseInt(e.target.value))}
            className="dashboard-select"
          >
            <option value="10">Refresh every 10s</option>
            <option value="30">Refresh every 30s</option>
            <option value="60">Refresh every 60s</option>
          </select>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="dashboard-metrics">
        <div className="metric-card">
          <div className="metric-icon">🌡️</div>
          <div className="metric-content">
            <div className="metric-label">Avg Temperature</div>
            <div className="metric-value">{stats.avgTemp}°C</div>
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-icon">📊</div>
          <div className="metric-content">
            <div className="metric-label">Active Components</div>
            <div className="metric-value">{stats.activeComponents}</div>
          </div>
        </div>
        <div className="metric-card warning">
          <div className="metric-icon">⚠️</div>
          <div className="metric-content">
            <div className="metric-label">Alerts</div>
            <div className="metric-value">{stats.totalAlerts}</div>
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-icon">🔥</div>
          <div className="metric-content">
            <div className="metric-label">Max Temperature</div>
            <div className="metric-value">{stats.maxTemp}°C</div>
          </div>
        </div>
      </div>

      {/* Production Lines */}
      <div className="dashboard-section">
        <h3>Production Lines Status</h3>
        <div className="production-lines">
          {Object.entries(lineMetrics).map(([line, metrics]) => (
            <div key={line} className="line-card">
              <div className="line-header">
                <h4>{line}</h4>
                <span className="component-count">{metrics.components} components</span>
              </div>
              <div className="line-metrics">
                <div className="line-metric healthy">
                  <span className="metric-dot"></span>
                  <span>Healthy: {metrics.healthy}</span>
                </div>
                <div className="line-metric warning">
                  <span className="metric-dot"></span>
                  <span>Warnings: {metrics.warnings}</span>
                </div>
                <div className="line-metric critical">
                  <span className="metric-dot"></span>
                  <span>Critical: {metrics.critical}</span>
                </div>
              </div>
              <div className="line-progress">
                <div
                  className="progress-bar healthy"
                  style={{ width: `${(metrics.healthy / metrics.components) * 100}%` }}
                ></div>
                <div
                  className="progress-bar warning"
                  style={{ width: `${(metrics.warnings / metrics.components) * 100}%` }}
                ></div>
                <div
                  className="progress-bar critical"
                  style={{ width: `${(metrics.critical / metrics.components) * 100}%` }}
                ></div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Activity */}
      <div className="dashboard-section">
        <h3>Recent Activity</h3>
        <div className="activity-list">
          {telemetryData.slice(0, 5).map((item, idx) => (
            <div key={idx} className="activity-item">
              <div className="activity-time">{new Date().toLocaleTimeString()}</div>
              <div className="activity-content">
                <span className="activity-component">{item.component_id}</span>
                <span className="activity-desc">
                  {item.sensorAReading > 180 ? '🚨 Critical temperature alert' :
                   item.sensorAReading > 150 ? '⚠️ Warning threshold exceeded' :
                   '✅ Operating normally'}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* System Health */}
      <div className="dashboard-section">
        <h3>System Health</h3>
        <div className="health-indicators">
          <div className="health-item">
            <div className="health-label">Database Connection</div>
            <div className="health-status healthy">✅ Connected</div>
          </div>
          <div className="health-item">
            <div className="health-label">Data Freshness</div>
            <div className="health-status healthy">✅ Real-time</div>
          </div>
          <div className="health-item">
            <div className="health-label">Compute Status</div>
            <div className="health-status healthy">✅ Active</div>
          </div>
          <div className="health-item">
            <div className="health-label">Last Update</div>
            <div className="health-status">{new Date().toLocaleTimeString()}</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
