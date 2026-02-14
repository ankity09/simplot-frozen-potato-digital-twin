import React, { useState, useEffect } from 'react';
import './SystemLogs.css';

const SystemLogs = ({ telemetryData, graphData }) => {
  const [logFilter, setLogFilter] = useState('all');
  const [selectedComponent, setSelectedComponent] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  // Generate system logs from telemetry data
  const generateLogs = () => {
    if (!telemetryData || telemetryData.length === 0) {
      return [];
    }

    const logs = [];
    const now = new Date();

    telemetryData.forEach((item, idx) => {
      const timestamp = new Date(now.getTime() - (idx * 5000)); // 5 seconds apart
      const temp = item.sensorAReading || 0;

      // Generate different log types based on temperature
      if (temp > 180) {
        logs.push({
          id: `log-${idx}-critical`,
          timestamp,
          level: 'critical',
          component: item.component_id,
          message: `Critical temperature threshold exceeded: ${temp}°C (threshold: 180°C)`,
          action: 'Automated alert sent to maintenance team',
        });
      } else if (temp > 170) {
        logs.push({
          id: `log-${idx}-warning`,
          timestamp,
          level: 'warning',
          component: item.component_id,
          message: `Temperature approaching critical threshold: ${temp}°C`,
          action: 'Monitoring system activated',
        });
      } else if (temp > 160) {
        logs.push({
          id: `log-${idx}-info`,
          timestamp,
          level: 'info',
          component: item.component_id,
          message: `Temperature reading: ${temp}°C - Within normal operating range`,
          action: 'No action required',
        });
      } else {
        logs.push({
          id: `log-${idx}-debug`,
          timestamp,
          level: 'debug',
          component: item.component_id,
          message: `Routine sensor reading: ${temp}°C`,
          action: 'Data logged to system',
        });
      }
    });

    return logs.sort((a, b) => b.timestamp - a.timestamp);
  };

  const allLogs = generateLogs();

  // Filter logs based on criteria
  const filteredLogs = allLogs.filter(log => {
    const matchesFilter = logFilter === 'all' || log.level === logFilter;
    const matchesComponent = selectedComponent === 'all' || log.component === selectedComponent;
    const matchesSearch = searchTerm === '' ||
      log.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.component.toLowerCase().includes(searchTerm.toLowerCase());

    return matchesFilter && matchesComponent && matchesSearch;
  });

  // Get unique components for filter
  const uniqueComponents = ['all', ...new Set(telemetryData.map(t => t.component_id))];

  // Calculate log level counts
  const logCounts = {
    critical: allLogs.filter(l => l.level === 'critical').length,
    warning: allLogs.filter(l => l.level === 'warning').length,
    info: allLogs.filter(l => l.level === 'info').length,
    debug: allLogs.filter(l => l.level === 'debug').length,
  };

  return (
    <div className="logs-container">
      <div className="logs-header">
        <h2>📋 System Logs</h2>
        <div className="logs-stats">
          <div className="stat-badge critical">{logCounts.critical} Critical</div>
          <div className="stat-badge warning">{logCounts.warning} Warnings</div>
          <div className="stat-badge info">{logCounts.info} Info</div>
          <div className="stat-badge debug">{logCounts.debug} Debug</div>
        </div>
      </div>

      {/* Filters */}
      <div className="logs-filters">
        <div className="filter-group">
          <label>Log Level:</label>
          <select
            value={logFilter}
            onChange={(e) => setLogFilter(e.target.value)}
            className="logs-select"
          >
            <option value="all">All Levels</option>
            <option value="critical">🔴 Critical</option>
            <option value="warning">🟡 Warning</option>
            <option value="info">🔵 Info</option>
            <option value="debug">⚪ Debug</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Component:</label>
          <select
            value={selectedComponent}
            onChange={(e) => setSelectedComponent(e.target.value)}
            className="logs-select"
          >
            {uniqueComponents.map(comp => (
              <option key={comp} value={comp}>
                {comp === 'all' ? 'All Components' : comp}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group search-group">
          <label>Search:</label>
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search logs..."
            className="logs-search"
          />
        </div>
      </div>

      {/* Log Statistics */}
      <div className="logs-section">
        <h3>📊 Log Summary</h3>
        <div className="log-summary">
          <div className="summary-item">
            <div className="summary-label">Total Logs</div>
            <div className="summary-value">{allLogs.length}</div>
          </div>
          <div className="summary-item">
            <div className="summary-label">Filtered Results</div>
            <div className="summary-value">{filteredLogs.length}</div>
          </div>
          <div className="summary-item">
            <div className="summary-label">Time Range</div>
            <div className="summary-value">Last Hour</div>
          </div>
          <div className="summary-item">
            <div className="summary-label">Active Components</div>
            <div className="summary-value">{uniqueComponents.length - 1}</div>
          </div>
        </div>
      </div>

      {/* Log Entries */}
      <div className="logs-section">
        <h3>📝 Log Entries ({filteredLogs.length})</h3>
        <div className="logs-list">
          {filteredLogs.length === 0 ? (
            <div className="no-logs">
              <div className="no-logs-icon">🔍</div>
              <div className="no-logs-text">No logs match your current filters</div>
            </div>
          ) : (
            filteredLogs.map((log) => (
              <div key={log.id} className={`log-entry ${log.level}`}>
                <div className="log-header">
                  <div className="log-level-badge">
                    {log.level === 'critical' && '🔴 CRITICAL'}
                    {log.level === 'warning' && '🟡 WARNING'}
                    {log.level === 'info' && '🔵 INFO'}
                    {log.level === 'debug' && '⚪ DEBUG'}
                  </div>
                  <div className="log-timestamp">
                    {log.timestamp.toLocaleTimeString()} - {log.timestamp.toLocaleDateString()}
                  </div>
                </div>
                <div className="log-body">
                  <div className="log-component">
                    <strong>Component:</strong> {log.component}
                  </div>
                  <div className="log-message">{log.message}</div>
                  {log.action && (
                    <div className="log-action">
                      <strong>Action:</strong> {log.action}
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Export Options */}
      <div className="logs-footer">
        <button className="export-button">📥 Export Logs (CSV)</button>
        <button className="export-button">📄 Export Logs (JSON)</button>
        <button className="clear-button">🗑️ Clear Filters</button>
      </div>
    </div>
  );
};

export default SystemLogs;
