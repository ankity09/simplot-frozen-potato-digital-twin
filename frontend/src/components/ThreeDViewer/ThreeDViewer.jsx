import React, { useRef, useState, useEffect, Suspense } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Text, Html, Box, Sphere, PerspectiveCamera, Environment } from '@react-three/drei';
import './ThreeDViewer.css';

// Animated product flowing through the line
const ProductFlow = ({ position, lineColor }) => {
  const meshRef = useRef();

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.position.x = position[0] + Math.sin(state.clock.elapsedTime * 2) * 0.3;
      meshRef.current.rotation.y += 0.05;
    }
  });

  return (
    <mesh ref={meshRef} position={position}>
      <sphereGeometry args={[0.15, 16, 16]} />
      <meshStandardMaterial color={lineColor} metalness={0.8} roughness={0.2} emissive={lineColor} emissiveIntensity={0.3} />
    </mesh>
  );
};

// Component representing a single equipment component with enhanced visuals
const FactoryComponent = ({ position, label, health, onClick, componentId, lineColor }) => {
  const meshRef = useRef();
  const [hovered, setHovered] = useState(false);
  const [pulsing, setPulsing] = useState(false);

  useFrame((state) => {
    if (meshRef.current) {
      // Subtle rotation when hovered
      if (hovered) {
        meshRef.current.rotation.y += 0.02;
      }
      // Pulsing effect for critical components
      if (health === 'critical') {
        const pulse = Math.sin(state.clock.elapsedTime * 3) * 0.1 + 1;
        meshRef.current.scale.set(pulse, pulse, pulse);
      }
    }
  });

  // Color based on health status with more vibrant colors
  const getColor = () => {
    if (health === 'critical') return '#ff4444';
    if (health === 'warning') return '#ffaa00';
    if (health === 'healthy') return '#44ff88';
    return '#888888';
  };

  const getEmissiveIntensity = () => {
    if (health === 'critical') return 0.6;
    if (health === 'warning') return 0.4;
    return 0.2;
  };

  return (
    <group position={position}>
      {/* Main equipment box */}
      <Box
        ref={meshRef}
        args={[0.9, 1.4, 0.9]}
        onPointerOver={(e) => { e.stopPropagation(); setHovered(true); }}
        onPointerOut={() => setHovered(false)}
        onClick={(e) => { e.stopPropagation(); onClick(componentId, label); }}
        scale={hovered ? 1.15 : 1}
      >
        <meshStandardMaterial
          color={getColor()}
          emissive={getColor()}
          emissiveIntensity={getEmissiveIntensity()}
          metalness={0.5}
          roughness={0.3}
        />
      </Box>

      {/* Base platform */}
      <Box args={[1.2, 0.1, 1.2]} position={[0, -0.8, 0]}>
        <meshStandardMaterial color="#1a1a2e" metalness={0.8} roughness={0.2} />
      </Box>

      {/* Control panel indicator */}
      <Box args={[0.3, 0.3, 0.05]} position={[0.5, 0, 0.46]}>
        <meshStandardMaterial color="#333" metalness={0.9} roughness={0.1} />
      </Box>

      {/* Status light */}
      <Sphere args={[0.08, 16, 16]} position={[0.5, 0.2, 0.48]}>
        <meshStandardMaterial
          color={getColor()}
          emissive={getColor()}
          emissiveIntensity={1.5}
        />
      </Sphere>

      {/* Component label using HTML for better rendering */}
      <Html position={[0, 1.2, 0]} center style={{ pointerEvents: 'none' }}>
        <div style={{
          background: 'rgba(0, 0, 0, 0.8)',
          padding: '4px 12px',
          borderRadius: '4px',
          color: 'white',
          fontSize: '14px',
          fontWeight: 'bold',
          whiteSpace: 'nowrap',
          border: `1px solid ${lineColor}`,
          boxShadow: '0 2px 8px rgba(0,0,0,0.5)'
        }}>
          {label}
        </div>
      </Html>

      {/* Stage label below using HTML */}
      <Html position={[0, -1.2, 0]} center style={{ pointerEvents: 'none' }}>
        <div style={{
          color: '#aaaaaa',
          fontSize: '12px',
          fontWeight: '500',
          whiteSpace: 'nowrap',
          textShadow: '0 0 4px #000'
        }}>
          {componentId.split('-')[1]}
        </div>
      </Html>

      {/* Info tooltip on hover */}
      {hovered && (
        <Html position={[0, 2.2, 0]} center style={{ pointerEvents: 'none' }}>
          <div className="component-tooltip">
            <strong>{componentId}</strong>
            <div className={`status-badge ${health}`}>
              {health === 'critical' && '🔴 Critical Alert'}
              {health === 'warning' && '🟡 Warning'}
              {health === 'healthy' && '🟢 Operational'}
            </div>
          </div>
        </Html>
      )}
    </group>
  );
};

// Enhanced Processing Stage with more details
const ProcessingStage = ({ position, label, components, onClick, lineColor }) => {
  return (
    <group position={position}>
      {/* Stage platform with line color accent */}
      <Box args={[3.5, 0.15, 2.5]} position={[0, -0.85, 0]}>
        <meshStandardMaterial color={lineColor} metalness={0.6} roughness={0.4} emissive={lineColor} emissiveIntensity={0.2} />
      </Box>

      {/* Stage base */}
      <Box args={[3.2, 0.08, 2.2]} position={[0, -0.92, 0]}>
        <meshStandardMaterial color="#2a2a3e" metalness={0.5} roughness={0.5} />
      </Box>

      {/* Stage label using HTML */}
      <Html position={[0, 0.9, 1.4]} center style={{ pointerEvents: 'none' }}>
        <div style={{
          background: `linear-gradient(135deg, ${lineColor}dd, ${lineColor}99)`,
          padding: '8px 20px',
          borderRadius: '6px',
          color: 'white',
          fontSize: '16px',
          fontWeight: 'bold',
          whiteSpace: 'nowrap',
          border: `2px solid ${lineColor}`,
          boxShadow: '0 4px 12px rgba(0,0,0,0.6)',
          textTransform: 'uppercase',
          letterSpacing: '1px'
        }}>
          {label}
        </div>
      </Html>

      {/* Components in this stage */}
      {components.map((comp, idx) => (
        <FactoryComponent
          key={comp.id}
          position={[(idx - components.length / 2) * 1.2, 0, 0]}
          label={comp.label}
          health={comp.health}
          onClick={onClick}
          componentId={comp.id}
          lineColor={lineColor}
        />
      ))}
    </group>
  );
};

// Enhanced Production Line with side-by-side layout
const ProductionLine = ({ lineData, position, onClick, showFlow }) => {
  return (
    <group position={position}>
      {/* Line base - longer for side-by-side layout */}
      <Box args={[28, 0.25, 5]} position={[0, -1.6, 0]}>
        <meshStandardMaterial
          color={lineData.color}
          metalness={0.7}
          roughness={0.3}
          emissive={lineData.color}
          emissiveIntensity={0.15}
        />
      </Box>

      {/* Line name using HTML for clarity */}
      <Html position={[-11, 1.8, 2.7]} center style={{ pointerEvents: 'none' }}>
        <div style={{
          background: `linear-gradient(135deg, ${lineData.color}, ${lineData.color}cc)`,
          padding: '12px 30px',
          borderRadius: '8px',
          color: 'white',
          fontSize: '20px',
          fontWeight: 'bold',
          whiteSpace: 'nowrap',
          border: `3px solid ${lineData.color}`,
          boxShadow: '0 6px 16px rgba(0,0,0,0.7)',
          textTransform: 'uppercase',
          letterSpacing: '2px',
          textShadow: '0 2px 4px rgba(0,0,0,0.5)'
        }}>
          {lineData.name}
        </div>
      </Html>

      {/* Processing stages along the line */}
      {lineData.stages.map((stage, idx) => (
        <ProcessingStage
          key={stage.id}
          position={[-10 + idx * 4.8, 0, 0]}
          label={stage.label}
          components={stage.components}
          onClick={onClick}
          lineColor={lineData.color}
        />
      ))}

      {/* Enhanced connection pipes between stages */}
      {lineData.stages.map((_, idx) => {
        if (idx < lineData.stages.length - 1) {
          return (
            <group key={`pipe-${idx}`}>
              {/* Main pipe */}
              <Box
                args={[3, 0.12, 0.12]}
                position={[-7.6 + idx * 4.8, -0.3, 0]}
              >
                <meshStandardMaterial color="#888888" metalness={0.9} roughness={0.1} />
              </Box>
              {/* Support brackets */}
              <Box args={[0.1, 0.3, 0.1]} position={[-9 + idx * 4.8, -0.5, 0]}>
                <meshStandardMaterial color="#555555" metalness={0.8} roughness={0.2} />
              </Box>
              <Box args={[0.1, 0.3, 0.1]} position={[-6.2 + idx * 4.8, -0.5, 0]}>
                <meshStandardMaterial color="#555555" metalness={0.8} roughness={0.2} />
              </Box>

              {/* Product flow animation */}
              {showFlow && (
                <>
                  <ProductFlow position={[-8.5 + idx * 4.8, -0.3, 0]} lineColor={lineData.color} />
                  <ProductFlow position={[-7 + idx * 4.8, -0.3, 0]} lineColor={lineData.color} />
                </>
              )}
            </group>
          );
        }
        return null;
      })}
    </group>
  );
};

// Enhanced Factory Floor with grid and details
const FactoryFloor = () => {
  return (
    <group>
      {/* Main floor */}
      <Box args={[80, 0.2, 45]} position={[0, -2.3, 0]}>
        <meshStandardMaterial
          color="#1a1a2e"
          metalness={0.2}
          roughness={0.8}
        />
      </Box>

      {/* Grid lines on floor */}
      <gridHelper args={[80, 40, '#2a4a7c', '#1a2a4c']} position={[0, -2.19, 0]} />

      {/* Factory walls (subtle background) */}
      <Box args={[80, 15, 0.5]} position={[0, 5, -22.5]}>
        <meshStandardMaterial color="#0a0a1a" metalness={0.1} roughness={0.9} transparent opacity={0.7} />
      </Box>
    </group>
  );
};

// Main Scene with improved camera and lighting
const FactoryScene = ({ productionLines, onComponentClick, showFlow, cameraRef }) => {
  return (
    <>
      <PerspectiveCamera
        ref={cameraRef}
        makeDefault
        position={[0, 18, 35]}
        fov={55}
      />
      <OrbitControls
        enableDamping
        dampingFactor={0.05}
        minDistance={15}
        maxDistance={60}
        maxPolarAngle={Math.PI / 2.1}
        target={[0, 0, 0]}
      />

      {/* Enhanced Lighting */}
      <ambientLight intensity={0.5} />
      <directionalLight position={[20, 20, 10]} intensity={1.2} castShadow />
      <directionalLight position={[-20, 15, -10]} intensity={0.6} />
      <pointLight position={[0, 15, 0]} intensity={0.8} distance={50} />
      <spotLight position={[10, 20, 10]} angle={0.3} penumbra={1} intensity={0.8} castShadow />
      <hemisphereLight color="#ffffff" groundColor="#1a2a4a" intensity={0.4} />

      {/* Environment for reflections */}
      <Environment preset="city" />

      {/* Factory Floor */}
      <FactoryFloor />

      {/* Production Lines - side by side instead of stacked */}
      {productionLines.map((line, idx) => (
        <ProductionLine
          key={line.id}
          lineData={line}
          position={[0, idx * 0, idx * -14]}  // Space them along Z-axis (front to back)
          onClick={onComponentClick}
          showFlow={showFlow}
        />
      ))}
    </>
  );
};

// Main Component with enhanced controls
const ThreeDViewer = ({ telemetryData = [], graphData = {} }) => {
  const [selectedComponent, setSelectedComponent] = useState(null);
  const [showFlow, setShowFlow] = useState(true);
  const cameraRef = useRef();

  // Generate factory data from telemetry and graph
  const generateFactoryData = () => {
    const getHealthStatus = (componentId) => {
      const telemetry = telemetryData.find(t => t.component_id === componentId);
      if (!telemetry) return 'unknown';

      const temp = telemetry.sensorAReading || 0;
      if (temp > 180) return 'critical';
      if (temp > 170) return 'warning';
      return 'healthy';
    };

    return [
      {
        id: 'line-ff',
        name: 'French Fries',
        color: '#3498db',
        stages: [
          {
            id: 'ff-wash',
            label: 'Washing',
            components: [{ id: 'FF-WASH', label: 'FF-WASH', health: getHealthStatus('FF-WASH') }]
          },
          {
            id: 'ff-peel',
            label: 'Peeling',
            components: [{ id: 'FF-PEEL', label: 'FF-PEEL', health: getHealthStatus('FF-PEEL') }]
          },
          {
            id: 'ff-cut',
            label: 'Cutting',
            components: [{ id: 'FF-CUT', label: 'FF-CUT', health: getHealthStatus('FF-CUT') }]
          },
          {
            id: 'ff-blanch',
            label: 'Blanching',
            components: [{ id: 'FF-BLANCH', label: 'FF-BLANCH', health: getHealthStatus('FF-BLANCH') }]
          },
          {
            id: 'ff-fry',
            label: 'Frying',
            components: [{ id: 'FF-FRY', label: 'FF-FRY', health: getHealthStatus('FF-FRY') }]
          },
          {
            id: 'ff-iqf',
            label: 'IQF Freezing',
            components: [{ id: 'FF-IQF', label: 'FF-IQF', health: getHealthStatus('FF-IQF') }]
          }
        ]
      },
      {
        id: 'line-hb',
        name: 'Hash Browns',
        color: '#e67e22',
        stages: [
          {
            id: 'hb-wash',
            label: 'Washing',
            components: [{ id: 'HB-WASH', label: 'HB-WASH', health: getHealthStatus('HB-WASH') }]
          },
          {
            id: 'hb-peel',
            label: 'Peeling',
            components: [{ id: 'HB-PEEL', label: 'HB-PEEL', health: getHealthStatus('HB-PEEL') }]
          },
          {
            id: 'hb-shred',
            label: 'Shredding',
            components: [{ id: 'HB-SHRED', label: 'HB-SHRED', health: getHealthStatus('HB-SHRED') }]
          },
          {
            id: 'hb-form',
            label: 'Forming',
            components: [{ id: 'HB-FORM', label: 'HB-FORM', health: getHealthStatus('HB-FORM') }]
          },
          {
            id: 'hb-iqf',
            label: 'IQF Freezing',
            components: [{ id: 'HB-IQF', label: 'HB-IQF', health: getHealthStatus('HB-IQF') }]
          }
        ]
      },
      {
        id: 'line-wg',
        name: 'Wedges',
        color: '#9b59b6',
        stages: [
          {
            id: 'wg-wash',
            label: 'Washing',
            components: [{ id: 'WG-WASH', label: 'WG-WASH', health: getHealthStatus('WG-WASH') }]
          },
          {
            id: 'wg-cut',
            label: 'Cutting',
            components: [{ id: 'WG-CUT', label: 'WG-CUT', health: getHealthStatus('WG-CUT') }]
          },
          {
            id: 'wg-season',
            label: 'Seasoning',
            components: [{ id: 'WG-SEASON', label: 'WG-SEASON', health: getHealthStatus('WG-SEASON') }]
          },
          {
            id: 'wg-fry',
            label: 'Frying',
            components: [{ id: 'WG-FRY', label: 'WG-FRY', health: getHealthStatus('WG-FRY') }]
          },
          {
            id: 'wg-iqf',
            label: 'IQF Freezing',
            components: [{ id: 'WG-IQF', label: 'WG-IQF', health: getHealthStatus('WG-IQF') }]
          }
        ]
      }
    ];
  };

  const productionLines = generateFactoryData();

  const handleComponentClick = (componentId, label) => {
    const telemetry = telemetryData.find(t => t.component_id === componentId);
    setSelectedComponent({
      id: componentId,
      label: label,
      telemetry: telemetry
    });
  };

  const handleClosePanel = () => {
    setSelectedComponent(null);
  };

  const resetCamera = () => {
    if (cameraRef.current) {
      cameraRef.current.position.set(0, 18, 35);
      cameraRef.current.lookAt(0, 0, 0);
    }
  };

  const focusLine = (lineIndex) => {
    if (cameraRef.current) {
      const zPositions = [0, -14, -28];
      cameraRef.current.position.set(0, 12, zPositions[lineIndex] + 20);
    }
  };

  return (
    <div className="threed-viewer">
      <div className="viewer-header">
        <h3>🏭 3D Factory Model</h3>
        <div className="viewer-controls">
          <button onClick={() => focusLine(0)}>
            📐 French Fries
          </button>
          <button onClick={() => focusLine(1)}>
            📐 Hash Browns
          </button>
          <button onClick={() => focusLine(2)}>
            📐 Wedges
          </button>
          <button onClick={resetCamera}>
            🔄 Reset View
          </button>
          <button
            onClick={() => setShowFlow(!showFlow)}
            className={showFlow ? 'active' : ''}
          >
            {showFlow ? '⏸️ Pause Flow' : '▶️ Show Flow'}
          </button>
          <div className="legend">
            <span className="legend-item healthy">🟢 Healthy</span>
            <span className="legend-item warning">🟡 Warning</span>
            <span className="legend-item critical">🔴 Critical</span>
          </div>
        </div>
      </div>

      <div className="canvas-container">
        <Canvas shadows gl={{ antialias: true, alpha: false }}>
          <Suspense fallback={null}>
            <FactoryScene
              productionLines={productionLines}
              onComponentClick={handleComponentClick}
              showFlow={showFlow}
              cameraRef={cameraRef}
            />
          </Suspense>
        </Canvas>
      </div>

      {selectedComponent && (
        <div className="component-panel">
          <div className="panel-header">
            <h4>{selectedComponent.label}</h4>
            <button onClick={handleClosePanel}>✕</button>
          </div>
          <div className="panel-content">
            <div className="telemetry-data">
              {selectedComponent.telemetry ? (
                <>
                  <div className="data-row">
                    <span className="label">Component ID:</span>
                    <span className="value">{selectedComponent.id}</span>
                  </div>
                  <div className="data-row">
                    <span className="label">Oil Temperature:</span>
                    <span className="value">
                      {selectedComponent.telemetry.oil_temperature?.toFixed(1) || 'N/A'}°C
                    </span>
                  </div>
                  <div className="data-row">
                    <span className="label">Water Temperature:</span>
                    <span className="value">
                      {selectedComponent.telemetry.water_temperature?.toFixed(1) || 'N/A'}°C
                    </span>
                  </div>
                  <div className="data-row">
                    <span className="label">Belt Speed:</span>
                    <span className="value">
                      {selectedComponent.telemetry.belt_speed?.toFixed(2) || 'N/A'} m/s
                    </span>
                  </div>
                  <div className="data-row">
                    <span className="label">Freezer Temp:</span>
                    <span className="value">
                      {selectedComponent.telemetry.freezer_temperature?.toFixed(1) || 'N/A'}°C
                    </span>
                  </div>
                  <div className="data-row">
                    <span className="label">Moisture Content:</span>
                    <span className="value">
                      {selectedComponent.telemetry.moisture_content?.toFixed(1) || 'N/A'}%
                    </span>
                  </div>
                  <div className="data-row">
                    <span className="label">Product Weight:</span>
                    <span className="value">
                      {selectedComponent.telemetry.product_weight?.toFixed(0) || 'N/A'} g
                    </span>
                  </div>
                  <div className="data-row">
                    <span className="label">Status:</span>
                    <span className={`badge ${
                      selectedComponent.telemetry.oil_temperature > 180 ? 'critical' :
                      selectedComponent.telemetry.oil_temperature > 170 ? 'warning' : 'healthy'
                    }`}>
                      {selectedComponent.telemetry.oil_temperature > 180 ? '🔴 Critical' :
                       selectedComponent.telemetry.oil_temperature > 170 ? '🟡 Warning' : '🟢 Healthy'}
                    </span>
                  </div>
                </>
              ) : (
                <div className="no-data">
                  <p>⚠️ No telemetry data available for this component</p>
                  <p className="hint">Data may still be loading or component is offline</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="viewer-instructions">
        <p>🖱️ <strong>Left-click + drag</strong> to rotate | <strong>Right-click + drag</strong> to pan | <strong>Scroll</strong> to zoom</p>
        <p>🎯 <strong>Click on components</strong> to view detailed telemetry data</p>
        <p>📐 <strong>Use focus buttons</strong> to zoom into specific production lines</p>
      </div>
    </div>
  );
};

export default ThreeDViewer;
