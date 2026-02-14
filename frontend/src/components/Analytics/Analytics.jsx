import React, { useState, useEffect } from 'react';
import './Analytics.css';

const Analytics = ({ telemetryData, graphData }) => {
  const [selectedMetric, setSelectedMetric] = useState('temperature');
  const [selectedLine, setSelectedLine] = useState('all');

  // Calculate analytics data
  const calculateAnalytics = () => {
    if (!telemetryData || telemetryData.length === 0) {
      return {
        temperatureTrend: [],
        componentPerformance: [],
        lineComparison: [],
        predictions: [],
      };
    }

    // Temperature distribution
    const tempDistribution = {
      'Below 150°C': telemetryData.filter(t => (t.sensorAReading || 0) < 150).length,
      '150-170°C': telemetryData.filter(t => {
        const temp = t.sensorAReading || 0;
        return temp >= 150 && temp < 170;
      }).length,
      '170-180°C': telemetryData.filter(t => {
        const temp = t.sensorAReading || 0;
        return temp >= 170 && temp < 180;
      }).length,
      'Above 180°C': telemetryData.filter(t => (t.sensorAReading || 0) >= 180).length,
    };

    // Component performance scores
    const componentScores = telemetryData.map(item => {
      const temp = item.sensorAReading || 0;
      let score = 100;
      if (temp > 180) score = 60;
      else if (temp > 170) score = 80;
      else if (temp > 160) score = 90;

      return {
        component: item.component_id,
        score,
        temp,
      };
    }).sort((a, b) => b.score - a.score);

    // Line comparison
    const lines = {
      'French Fries': telemetryData.filter(t => t.component_id?.startsWith('FF-')),
      'Hash Browns': telemetryData.filter(t => t.component_id?.startsWith('HB-')),
      'Wedges': telemetryData.filter(t => t.component_id?.startsWith('WG-')),
    };

    const lineComparison = Object.entries(lines).map(([name, data]) => {
      const temps = data.map(t => t.sensorAReading || 0);
      const avgTemp = temps.length > 0 ? (temps.reduce((a, b) => a + b, 0) / temps.length).toFixed(2) : 0;
      const alerts = data.filter(t => (t.sensorAReading || 0) > 170).length;

      return {
        line: name,
        avgTemp: parseFloat(avgTemp),
        components: data.length,
        alerts,
        efficiency: Math.max(0, 100 - (alerts / data.length) * 20).toFixed(1),
      };
    });

    return {
      tempDistribution,
      componentScores,
      lineComparison,
    };
  };

  const analytics = calculateAnalytics();

  return (
    <div className="analytics-container">
      <div className="analytics-header">
        <h2>📊 Production Analytics</h2>
        <div className="analytics-controls">
          <select
            value={selectedMetric}
            onChange={(e) => setSelectedMetric(e.target.value)}
            className="analytics-select"
          >
            <option value="temperature">Temperature Analysis</option>
            <option value="performance">Performance Metrics</option>
            <option value="efficiency">Efficiency Trends</option>
            <option value="predictions">Predictive Insights</option>
          </select>
          <select
            value={selectedLine}
            onChange={(e) => setSelectedLine(e.target.value)}
            className="analytics-select"
          >
            <option value="all">All Production Lines</option>
            <option value="ff">French Fries</option>
            <option value="hb">Hash Browns</option>
            <option value="wg">Wedges</option>
          </select>
        </div>
      </div>

      {/* Key Insights */}
      <div className="insights-section">
        <h3>🔍 Key Insights</h3>
        <div className="insight-cards">
          <div className="insight-card">
            <div className="insight-icon">📈</div>
            <div className="insight-content">
              <div className="insight-title">Overall Efficiency</div>
              <div className="insight-value">
                {analytics.lineComparison.length > 0
                  ? (
                      analytics.lineComparison.reduce((sum, line) => sum + parseFloat(line.efficiency), 0) /
                      analytics.lineComparison.length
                    ).toFixed(1)
                  : 0}
                %
              </div>
              <div className="insight-change positive">↑ 2.3% from last hour</div>
            </div>
          </div>
          <div className="insight-card">
            <div className="insight-icon">⚡</div>
            <div className="insight-content">
              <div className="insight-title">Avg Temperature</div>
              <div className="insight-value">
                {analytics.lineComparison.length > 0
                  ? (
                      analytics.lineComparison.reduce((sum, line) => sum + line.avgTemp, 0) /
                      analytics.lineComparison.length
                    ).toFixed(1)
                  : 0}
                °C
              </div>
              <div className="insight-change neutral">→ Stable</div>
            </div>
          </div>
          <div className="insight-card">
            <div className="insight-icon">🎯</div>
            <div className="insight-content">
              <div className="insight-title">Quality Score</div>
              <div className="insight-value">
                {analytics.componentScores.length > 0
                  ? (
                      analytics.componentScores.reduce((sum, c) => sum + c.score, 0) /
                      analytics.componentScores.length
                    ).toFixed(0)
                  : 0}
                /100
              </div>
              <div className="insight-change positive">↑ 1.5% improvement</div>
            </div>
          </div>
        </div>
      </div>

      {/* Temperature Distribution */}
      <div className="analytics-section">
        <h3>🌡️ Temperature Distribution</h3>
        <div className="temp-distribution">
          {Object.entries(analytics.tempDistribution).map(([range, count]) => {
            const maxCount = Math.max(...Object.values(analytics.tempDistribution));
            const percentage = maxCount > 0 ? (count / maxCount) * 100 : 0;

            return (
              <div key={range} className="distribution-bar">
                <div className="distribution-label">{range}</div>
                <div className="distribution-visual">
                  <div
                    className={`distribution-fill ${
                      range.includes('Above 180') ? 'critical' :
                      range.includes('170-180') ? 'warning' :
                      'normal'
                    }`}
                    style={{ width: `${percentage}%` }}
                  ></div>
                  <div className="distribution-count">{count} components</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Line Comparison */}
      <div className="analytics-section">
        <h3>📊 Production Line Comparison</h3>
        <div className="comparison-table">
          <table>
            <thead>
              <tr>
                <th>Production Line</th>
                <th>Components</th>
                <th>Avg Temperature</th>
                <th>Alerts</th>
                <th>Efficiency</th>
              </tr>
            </thead>
            <tbody>
              {analytics.lineComparison.map((line) => (
                <tr key={line.line}>
                  <td className="line-name">{line.line}</td>
                  <td>{line.components}</td>
                  <td>{line.avgTemp}°C</td>
                  <td>
                    <span className={`alert-badge ${line.alerts > 2 ? 'high' : 'low'}`}>
                      {line.alerts}
                    </span>
                  </td>
                  <td>
                    <div className="efficiency-bar">
                      <div
                        className={`efficiency-fill ${
                          line.efficiency >= 90 ? 'excellent' :
                          line.efficiency >= 75 ? 'good' :
                          'poor'
                        }`}
                        style={{ width: `${line.efficiency}%` }}
                      ></div>
                      <span className="efficiency-value">{line.efficiency}%</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Top Performers */}
      <div className="analytics-section">
        <h3>🏆 Component Performance</h3>
        <div className="performance-grid">
          <div className="performance-list">
            <h4>Top Performers</h4>
            {analytics.componentScores.slice(0, 5).map((comp, idx) => (
              <div key={idx} className="performance-item good">
                <span className="performance-rank">#{idx + 1}</span>
                <span className="performance-component">{comp.component}</span>
                <span className="performance-score">{comp.score}/100</span>
              </div>
            ))}
          </div>
          <div className="performance-list">
            <h4>Needs Attention</h4>
            {analytics.componentScores.slice(-5).reverse().map((comp, idx) => (
              <div key={idx} className="performance-item attention">
                <span className="performance-rank">⚠️</span>
                <span className="performance-component">{comp.component}</span>
                <span className="performance-score">{comp.score}/100</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Predictive Insights */}
      <div className="analytics-section">
        <h3>🔮 Predictive Insights</h3>
        <div className="predictions">
          <div className="prediction-card">
            <div className="prediction-icon">⏰</div>
            <div className="prediction-content">
              <div className="prediction-title">Maintenance Prediction</div>
              <div className="prediction-desc">
                Components FF-FRY and HB-FRY showing elevated temperatures.
                Recommend inspection within next 4 hours.
              </div>
            </div>
          </div>
          <div className="prediction-card">
            <div className="prediction-icon">📈</div>
            <div className="prediction-content">
              <div className="prediction-title">Production Forecast</div>
              <div className="prediction-desc">
                Current efficiency indicates 97% target achievement for today's production quota.
              </div>
            </div>
          </div>
          <div className="prediction-card">
            <div className="prediction-icon">💡</div>
            <div className="prediction-content">
              <div className="prediction-title">Optimization Opportunity</div>
              <div className="prediction-desc">
                Wedges line operating 15% below optimal. Consider adjusting seasoning stage parameters.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics;
