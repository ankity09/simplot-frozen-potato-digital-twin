// DatabricksService removed for security - use TelemetryService backend proxy instead
import TelemetryService from '../services/telemetryService';

export class TelemetryFetcher {
  constructor() {
    // Removed insecure DatabricksService - frontend should never connect directly to Databricks
    // this.databricksService = new DatabricksService(); // ⚠️ REMOVED FOR SECURITY

    this.telemetryService = new TelemetryService(); // ✅ Secure backend proxy
    this.mockData = this.generateMockTelemetryData();
    this.useBackend = true; // Always use backend proxy (secure)

    console.log('✅ TelemetryFetcher: Using secure backend telemetry service');
    console.log('   Backend URL: ' + (this.telemetryService.backendBaseUrl || 'http://localhost:8080'));
    console.log('   Security: All Databricks authentication handled server-side with OAuth');
  }

  // Removed testDatabricksConnection() - direct connections are insecure
  // Backend handles all Databricks authentication via OAuth

  generateMockTelemetryData() {
    // Use actual component IDs from RDF triples data for better compatibility
    const components = ['FF-WASH', 'FF-PEEL', 'FF-CUT', 'FF-BLANCH', 'FF-FRY', 'FF-IQF', 'HB-WASH', 'HB-PEEL', 'HB-SHRED', 'HB-FORM', 'HB-IQF', 'WG-WASH', 'WG-CUT', 'WG-SEASON', 'WG-FRY', 'WG-IQF'];
    const data = [];

    const now = new Date();

    for (let i = 0; i < 100; i++) {
      const timestamp = new Date(now.getTime() - (i * 60000));

      components.forEach(componentID => {
        data.push({
          componentID,
          sensorAReading: 170 + Math.random() * 15,  // Oil Temperature ~170-185°C
          sensorBReading: 10 + Math.random() * 10,   // Water Temperature ~10-20°C
          sensorCReading: 1.0 + Math.random() * 1.0,  // Belt Speed ~1-2 m/s
          sensorDReading: -35 + Math.random() * 10,   // Freezer Temperature ~-35 to -25°C
          timestamp: timestamp.toISOString()
        });
      });
    }

    return data;
  }

  async fetchLatestTelemetry(componentID) {
    // Always use secure backend proxy
    try {
      console.log(`📡 Fetching telemetry for component ${componentID} via backend proxy`);
      const result = await this.telemetryService.fetchLatestTelemetry();

      if (result.success && result.data && result.data.length > 0) {
        const componentData = result.data.find(data => data.componentID === componentID);
        if (componentData) {
          console.log(`✅ Found telemetry data for component ${componentID}`);
          return componentData;
        } else {
          console.warn(`⚠️  No data for component ${componentID}. Available: ${result.data.map(d => d.componentID).join(', ')}`);
          return null;
        }
      } else {
        console.warn('⚠️  Backend returned no telemetry data, using mock data');
        throw new Error('No telemetry data from backend');
      }
    } catch (error) {
      console.error('❌ Backend unavailable, using mock data:', error.message);
    }

    // Fallback to mock data if backend unavailable
    console.log(`🎭 Using mock data for component: ${componentID}`);
    await this.simulateDelay();

    const componentData = this.mockData
      .filter(data => data.componentID === componentID)
      .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

    return componentData[0] || null;
  }

  async fetchHistoricalTelemetry(componentID, startTime, endTime) {
    // Use mock data for historical telemetry (backend endpoint for historical data can be added)
    console.log(`📊 Fetching historical telemetry for ${componentID} (${startTime} to ${endTime})`);
    await this.simulateDelay();

    const start = new Date(startTime);
    const end = new Date(endTime);

    return this.mockData
      .filter(data => {
        const dataTime = new Date(data.timestamp);
        return data.componentID === componentID &&
               dataTime >= start &&
               dataTime <= end;
      })
      .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
  }

  async fetchAllLatestTelemetry() {
    // Always use secure backend proxy
    try {
      console.log('📡 Fetching all latest telemetry via backend proxy');
      const result = await this.telemetryService.fetchLatestTelemetry();

      if (result.success && result.data && result.data.length > 0) {
        console.log(`✅ Retrieved ${result.data.length} telemetry records from backend`);
        return result.data;
      } else {
        console.warn('⚠️  Backend returned no telemetry data, using mock data');
        throw new Error('No telemetry data from backend');
      }
    } catch (error) {
      console.error('❌ Backend unavailable, using mock data:', error.message);
    }

    // Fallback to mock data if backend unavailable
    console.log('🎭 Using mock data for all latest telemetry');
    await this.simulateDelay();

    const latest = {};

    this.mockData.forEach(data => {
      if (!latest[data.componentID] ||
          new Date(data.timestamp) > new Date(latest[data.componentID].timestamp)) {
        latest[data.componentID] = data;
      }
    });

    return Object.values(latest);
  }

  async fetchTelemetryByTimeRange(startTime, endTime) {
    // Use mock data for time range queries (backend endpoint can be added)
    console.log(`📊 Fetching telemetry by time range (${startTime} to ${endTime})`);
    await this.simulateDelay();

    const start = new Date(startTime);
    const end = new Date(endTime);

    return this.mockData
      .filter(data => {
        const dataTime = new Date(data.timestamp);
        return dataTime >= start && dataTime <= end;
      })
      .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
  }

  simulateDelay() {
    return new Promise(resolve => setTimeout(resolve, Math.random() * 500 + 100));
  }

  getSensorDefinitions() {
    return {
      sensorAReading: { label: 'Oil Temperature', unit: '°C', min: 0, max: 200 },
      sensorBReading: { label: 'Water Temperature', unit: '°C', min: 0, max: 100 },
      sensorCReading: { label: 'Belt Speed', unit: 'm/s', min: 0, max: 3 },
      sensorDReading: { label: 'Freezer Temperature', unit: '°C', min: -50, max: 30 }
    };
  }

  getHealthThresholds() {
    return {
      sensorAReading: { warning: 182, critical: 190 },  // Oil temperature
      sensorBReading: { warning: 88, critical: 95 },     // Water temperature
      sensorCReading: { warning: 2.2, critical: 2.5 },   // Belt speed
      sensorDReading: { warning: -25, critical: -20 }     // Freezer temperature (warning when TOO WARM)
    };
  }

  analyzeSensorHealth(sensorValue, sensorType) {
    const thresholds = this.getHealthThresholds()[sensorType];
    if (!thresholds) return 'unknown';
    
    if (sensorValue >= thresholds.critical) return 'critical';
    if (sensorValue >= thresholds.warning) return 'warning';
    return 'healthy';
  }

  getComponentHealth(telemetryData) {
    if (!telemetryData) return 'unknown';
    
    const sensors = ['sensorAReading', 'sensorBReading', 'sensorCReading', 'sensorDReading'];
    const healthLevels = sensors.map(sensor => 
      this.analyzeSensorHealth(telemetryData[sensor], sensor)
    );
    
    if (healthLevels.includes('critical')) return 'critical';
    if (healthLevels.includes('warning')) return 'warning';
    return 'healthy';
  }
}