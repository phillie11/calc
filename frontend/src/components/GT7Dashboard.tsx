import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Camera, Sliders, Settings, Save, RefreshCw, BarChart2, Clock } from 'lucide-react';

const GT7Dashboard = () => {
  const [currentVehicle, setCurrentVehicle] = useState({
    name: 'Dodge Viper GTS',
    weight: 1542,
    power: 450,
    torque: 69.5,
    drivetrain: 'FR',
    maxRPM: 7000,
    pp: 589.4
  });
  
  const [activeTab, setActiveTab] = useState('overview');
  
  // Sample engine data for power curve
  const engineData = [
    { rpm: 1000, torque: 35, power: 47 },
    { rpm: 2000, torque: 55, power: 148 },
    { rpm: 3000, torque: 65, power: 261 },
    { rpm: 4000, torque: 68, power: 363 },
    { rpm: 5000, torque: 69.5, power: 412 },
    { rpm: 6000, torque: 64, power: 450 },
    { rpm: 7000, torque: 52, power: 392 },
  ];
  
  // Sample recently saved setups
  const recentSetups = [
    { id: 1, name: 'Nürburgring Setup', date: '2025-04-12', vehicle: 'Dodge Viper GTS', notes: 'Optimized for high-speed sections' },
    { id: 2, name: 'Tokyo Expressway', date: '2025-04-10', vehicle: 'Dodge Viper GTS', notes: 'Balanced grip for tight corners' },
    { id: 3, name: 'Sardegna', date: '2025-04-05', vehicle: 'Dodge Viper GTS', notes: 'Dirt track tuning' },
  ];
  
  // Sample suspension settings
  const suspensionSettings = {
    front: {
      springRate: 9.8,
      rideHeight: 120,
      compression: 30,
      extension: 40,
      camber: -3.0,
      toe: 0.05,
      antiRollBar: 6
    },
    rear: {
      springRate: 10.2,
      rideHeight: 130,
      compression: 32,
      extension: 38,
      camber: -2.0,
      toe: 0.20,
      antiRollBar: 5
    },
    frequency: {
      front: 2.15,
      rear: 2.28
    }
  };
  
  // Sample transmission settings
  const gearSettings = {
    final: 3.545,
    ratios: {
      '1st': 3.827,
      '2nd': 2.360,
      '3rd': 1.685,
      '4th': 1.312,
      '5th': 1.000,
      '6th': 0.793
    },
    topSpeed: 287,
    acceleration: 4.1
  };
  
  return (
    <div className="flex flex-col h-full bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 p-4">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <h1 className="text-xl font-bold bg-gradient-to-r from-blue-500 to-cyan-400 bg-clip-text text-transparent">
              GT7 Pro Tune Dashboard
            </h1>
            <span className="px-2 py-1 bg-blue-900 rounded text-xs">{currentVehicle.pp} PP</span>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-gray-400">{currentVehicle.name}</span>
            <button className="p-2 rounded bg-blue-800 hover:bg-blue-700 transition-colors">
              <RefreshCw size={16} />
            </button>
          </div>
        </div>
      </header>
      
      {/* Main Content */}
      <div className="flex-1 p-4 overflow-auto">
        {/* Tabs */}
        <div className="flex border-b border-gray-700 mb-4">
          <button 
            className={`px-4 py-2 font-medium ${activeTab === 'overview' ? 'text-blue-400 border-b-2 border-blue-400' : 'text-gray-400 hover:text-gray-200'}`}
            onClick={() => setActiveTab('overview')}
          >
            Overview
          </button>
          <button 
            className={`px-4 py-2 font-medium ${activeTab === 'suspension' ? 'text-blue-400 border-b-2 border-blue-400' : 'text-gray-400 hover:text-gray-200'}`}
            onClick={() => setActiveTab('suspension')}
          >
            Suspension
          </button>
          <button 
            className={`px-4 py-2 font-medium ${activeTab === 'transmission' ? 'text-blue-400 border-b-2 border-blue-400' : 'text-gray-400 hover:text-gray-200'}`}
            onClick={() => setActiveTab('transmission')}
          >
            Transmission
          </button>
          <button 
            className={`px-4 py-2 font-medium ${activeTab === 'saved' ? 'text-blue-400 border-b-2 border-blue-400' : 'text-gray-400 hover:text-gray-200'}`}
            onClick={() => setActiveTab('saved')}
          >
            Saved Setups
          </button>
        </div>
        
        {/* Tab Content */}
        <div className="mt-4">
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Vehicle Stats */}
              <div className="bg-gray-800 rounded-lg p-4">
                <h2 className="text-lg font-bold mb-4">Vehicle Information</h2>
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex flex-col">
                    <span className="text-gray-400 text-sm">Weight</span>
                    <span className="text-lg">{currentVehicle.weight} kg</span>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-gray-400 text-sm">Power</span>
                    <span className="text-lg">{currentVehicle.power} HP</span>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-gray-400 text-sm">Torque</span>
                    <span className="text-lg">{currentVehicle.torque} kg·m</span>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-gray-400 text-sm">Drivetrain</span>
                    <span className="text-lg">{currentVehicle.drivetrain}</span>
                  </div>
                </div>
              </div>
              
              {/* Quick Actions */}
              <div className="bg-gray-800 rounded-lg p-4">
                <h2 className="text-lg font-bold mb-4">Quick Actions</h2>
                <div className="grid grid-cols-2 gap-4">
                  <button className="flex items-center justify-center p-3 bg-blue-700 hover:bg-blue-600 rounded-lg transition-colors">
                    <Sliders size={16} className="mr-2" />
                    <span>Calculate Springs</span>
                  </button>
                  <button className="flex items-center justify-center p-3 bg-yellow-700 hover:bg-yellow-600 rounded-lg transition-colors">
                    <Settings size={16} className="mr-2" />
                    <span>Calculate Gears</span>
                  </button>
                  <button className="flex items-center justify-center p-3 bg-cyan-800 hover:bg-cyan-700 rounded-lg transition-colors">
                    <Camera size={16} className="mr-2" />
                    <span>Upload Screenshot</span>
                  </button>
                  <button className="flex items-center justify-center p-3 bg-green-800 hover:bg-green-700 rounded-lg transition-colors">
                    <Save size={16} className="mr-2" />
                    <span>Save Setup</span>
                  </button>
                </div>
              </div>
              
              {/* Power/Torque Chart */}
              <div className="bg-gray-800 rounded-lg p-4 md:col-span-2">
                <h2 className="text-lg font-bold mb-4">Power & Torque Curve</h2>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart
                      data={engineData}
                      margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                      <XAxis 
                        dataKey="rpm" 
                        label={{ value: 'RPM', position: 'insideBottomRight', offset: -10, fill: '#888' }} 
                        tick={{ fill: '#888' }}
                      />
                      <YAxis 
                        yAxisId="left" 
                        label={{ value: 'Power (HP)', angle: -90, position: 'insideLeft', fill: '#888' }} 
                        tick={{ fill: '#888' }}
                      />
                      <YAxis 
                        yAxisId="right" 
                        orientation="right" 
                        label={{ value: 'Torque (kg·m)', angle: -90, position: 'insideRight', fill: '#888' }} 
                        tick={{ fill: '#888' }}
                      />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#333', borderColor: '#555' }} 
                        labelStyle={{ color: '#fff' }}
                      />
                      <Legend />
                      <Line 
                        yAxisId="left" 
                        type="monotone" 
                        dataKey="power" 
                        stroke="#3b82f6" 
                        strokeWidth={2} 
                        dot={{ r: 3 }} 
                        activeDot={{ r: 5 }} 
                        name="Power"
                      />
                      <Line 
                        yAxisId="right" 
                        type="monotone" 
                        dataKey="torque" 
                        stroke="#ef4444" 
                        strokeWidth={2} 
                        dot={{ r: 3 }} 
                        activeDot={{ r: 5 }} 
                        name="Torque"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
              
              {/* Current Setup Summary */}
              <div className="bg-gray-800 rounded-lg p-4 md:col-span-2">
                <h2 className="text-lg font-bold mb-4">Current Setup Summary</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-gray-900 p-3 rounded-lg">
                    <h3 className="text-gray-400 text-sm mb-2">Suspension</h3>
                    <div className="flex justify-between mb-1">
                      <span className="text-gray-400">Front Springs:</span>
                      <span>{suspensionSettings.front.springRate} N/mm</span>
                    </div>
                    <div className="flex justify-between mb-1">
                      <span className="text-gray-400">Rear Springs:</span>
                      <span>{suspensionSettings.rear.springRate} N/mm</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">ARB (F/R):</span>
                      <span>{suspensionSettings.front.antiRollBar}/{suspensionSettings.rear.antiRollBar}</span>
                    </div>
                  </div>
                  <div className="bg-gray-900 p-3 rounded-lg">
                    <h3 className="text-gray-400 text-sm mb-2">Transmission</h3>
                    <div className="flex justify-between mb-1">
                      <span className="text-gray-400">Final Drive:</span>
                      <span>{gearSettings.final}</span>
                    </div>
                    <div className="flex justify-between mb-1">
                      <span className="text-gray-400">Top Speed:</span>
                      <span>{gearSettings.topSpeed} mph</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">0-60 mph:</span>
                      <span>{gearSettings.acceleration} sec</span>
                    </div>
                  </div>
                  <div className="bg-gray-900 p-3 rounded-lg">
                    <h3 className="text-gray-400 text-sm mb-2">Alignment</h3>
                    <div className="flex justify-between mb-1">
                      <span className="text-gray-400">Camber (F/R):</span>
                      <span>{suspensionSettings.front.camber}/{suspensionSettings.rear.camber}°</span>
                    </div>
                    <div className="flex justify-between mb-1">
                      <span className="text-gray-400">Toe (F/R):</span>
                      <span>{suspensionSettings.front.toe}/{suspensionSettings.rear.toe}°</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Ride Height (F/R):</span>
                      <span>{suspensionSettings.front.rideHeight}/{suspensionSettings.rear.rideHeight} mm</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {/* Suspension Tab */}
          {activeTab === 'suspension' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-gray-800 rounded-lg p-4">
                <h2 className="text-lg font-bold mb-4">Spring Rates</h2>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-gray-900 p-3 rounded-lg">
                    <h3 className="text-gray-400 text-sm mb-2">Front</h3>
                    <div className="text-2xl font-bold text-blue-400">{suspensionSettings.front.springRate} N/mm</div>
                    <div className="text-sm text-gray-400 mt-1">Frequency: {suspensionSettings.frequency.front} Hz</div>
                  </div>
                  <div className="bg-gray-900 p-3 rounded-lg">
                    <h3 className="text-gray-400 text-sm mb-2">Rear</h3>
                    <div className="text-2xl font-bold text-blue-400">{suspensionSettings.rear.springRate} N/mm</div>
                    <div className="text-sm text-gray-400 mt-1">Frequency: {suspensionSettings.frequency.rear} Hz</div>
                  </div>
                </div>
                <div className="mt-4">
                  <h3 className="text-gray-400 text-sm mb-2">Ride Height</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-gray-900 p-3 rounded-lg text-center">
                      <div className="text-xl font-bold">{suspensionSettings.front.rideHeight} mm</div>
                      <div className="text-xs text-gray-400 mt-1">Front</div>
                    </div>
                    <div className="bg-gray-900 p-3 rounded-lg text-center">
                      <div className="text-xl font-bold">{suspensionSettings.rear.rideHeight} mm</div>
                      <div className="text-xs text-gray-400 mt-1">Rear</div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-4">
                <h2 className="text-lg font-bold mb-4">Dampers</h2>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h3 className="text-gray-400 text-sm mb-2">Compression</h3>
                    <div className="grid grid-cols-2 gap-2">
                      <div className="bg-gray-900 p-2 rounded-lg text-center">
                        <div className="text-xl font-bold">{suspensionSettings.front.compression}</div>
                        <div className="text-xs text-gray-400 mt-1">Front</div>
                      </div>
                      <div className="bg-gray-900 p-2 rounded-lg text-center">
                        <div className="text-xl font-bold">{suspensionSettings.rear.compression}</div>
                        <div className="text-xs text-gray-400 mt-1">Rear</div>
                      </div>
                    </div>
                  </div>
                  <div>
                    <h3 className="text-gray-400 text-sm mb-2">Extension</h3>
                    <div className="grid grid-cols-2 gap-2">
                      <div className="bg-gray-900 p-2 rounded-lg text-center">
                        <div className="text-xl font-bold">{suspensionSettings.front.extension}</div>
                        <div className="text-xs text-gray-400 mt-1">Front</div>
                      </div>
                      <div className="bg-gray-900 p-2 rounded-lg text-center">
                        <div className="text-xl font-bold">{suspensionSettings.rear.extension}</div>
                        <div className="text-xs text-gray-400 mt-1">Rear</div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <h3 className="text-gray-400 text-sm mb-2 mt-4">Anti-Roll Bars</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-gray-900 p-3 rounded-lg text-center">
                    <div className="text-xl font-bold">{suspensionSettings.front.antiRollBar}</div>
                    <div className="text-xs text-gray-400 mt-1">Front</div>
                  </div>
                  <div className="bg-gray-900 p-3 rounded-lg text-center">
                    <div className="text-xl font-bold">{suspensionSettings.rear.antiRollBar}</div>
                    <div className="text-xs text-gray-400 mt-1">Rear</div>
                  </div>
                </div>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-4 md:col-span-2">
                <h2 className="text-lg font-bold mb-4">Alignment</h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <h3 className="text-gray-400 text-sm mb-2">Camber</h3>
                    <div className="grid grid-cols-2 gap-2">
                      <div className="bg-gray-900 p-2 rounded-lg text-center">
                        <div className="text-xl font-bold">{suspensionSettings.front.camber}°</div>
                        <div className="text-xs text-gray-400 mt-1">Front</div>
                      </div>
                      <div className="bg-gray-900 p-2 rounded-lg text-center">
                        <div className="text-xl font-bold">{suspensionSettings.rear.camber}°</div>
                        <div className="text-xs text-gray-400 mt-1">Rear</div>
                      </div>
                    </div>
                  </div>
                  <div>
                    <h3 className="text-gray-400 text-sm mb-2">Toe</h3>
                    <div className="grid grid-cols-2 gap-2">
                      <div className="bg-gray-900 p-2 rounded-lg text-center">
                        <div className="text-xl font-bold">{suspensionSettings.front.toe}°</div>
                        <div className="text-xs text-gray-400 mt-1">Front</div>
                      </div>
                      <div className="bg-gray-900 p-2 rounded-lg text-center">
                        <div className="text-xl font-bold">{suspensionSettings.rear.toe}°</div>
                        <div className="text-xs text-gray-400 mt-1">Rear</div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="mt-6">
                  <h3 className="text-gray-400 text-sm mb-3">Stability & G-Force Values</h3>
                  <div className="grid grid-cols-3 md:grid-cols-5 gap-3">
                    <div className="bg-gray-900 p-2 rounded-lg text-center">
                      <div className="text-xs text-gray-400 mb-1">Low Speed Stability</div>
                      <div className="text-lg font-bold">0.00</div>
                    </div>
                    <div className="bg-gray-900 p-2 rounded-lg text-center">
                      <div className="text-xs text-gray-400 mb-1">High Speed Stability</div>
                      <div className="text-lg font-bold">1.00</div>
                    </div>
                    <div className="bg-gray-900 p-2 rounded-lg text-center">
                      <div className="text-xs text-gray-400 mb-1">G @ 40mph</div>
                      <div className="text-lg font-bold">0.90</div>
                    </div>
                    <div className="bg-gray-900 p-2 rounded-lg text-center">
                      <div className="text-xs text-gray-400 mb-1">G @ 75mph</div>
                      <div className="text-lg font-bold">0.95</div>
                    </div>
                    <div className="bg-gray-900 p-2 rounded-lg text-center">
                      <div className="text-xs text-gray-400 mb-1">G @ 150mph</div>
                      <div className="text-lg font-bold">0.85</div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-4 md:col-span-2">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-lg font-bold">Adjustment Settings</h2>
                  <button className="px-4 py-2 bg-blue-700 hover:bg-blue-600 rounded-lg transition-colors">
                    Recalculate
                  </button>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="text-gray-400 text-sm block mb-1">Stiffness Multiplier</label>
                    <div className="flex">
                      <input type="range" min="0.5" max="2" step="0.05" defaultValue="1" className="w-full" />
                      <span className="ml-2 text-gray-400">1.0</span>
                    </div>
                  </div>
                  <div>
                    <label className="text-gray-400 text-sm block mb-1">Oversteer/Understeer</label>
                    <div className="flex">
                      <input type="range" min="-5" max="5" defaultValue="0" className="w-full" />
                      <span className="ml-2 text-gray-400">0</span>
                    </div>
                  </div>
                  <div>
                    <label className="text-gray-400 text-sm block mb-1">Spring Frequency Offset</label>
                    <div className="flex">
                      <input type="range" min="-5" max="6" defaultValue="0" className="w-full" />
                      <span className="ml-2 text-gray-400">0</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {/* Transmission Tab */}
          {activeTab === 'transmission' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-gray-800 rounded-lg p-4">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-lg font-bold">Gear Ratios</h2>
                  <div className="flex items-center space-x-2">
                    <span className="text-gray-400 text-sm">Final Drive:</span>
                    <span className="font-bold">{gearSettings.final}</span>
                  </div>
                </div>
                
                <div className="space-y-2">
                  {Object.entries(gearSettings.ratios).map(([gear, ratio]) => (
                    <div key={gear} className="flex items-center">
                      <div className="w-12 text-gray-400">{gear}</div>
                      <div className="flex-1 bg-gray-900 rounded h-8 relative">
                        <div 
                          className="absolute top-0 left-0 h-full bg-gradient-to-r from-blue-900 to-blue-700 rounded"
                          style={{ width: `${(ratio / 4) * 100}%` }}
                        ></div>
                        <div className="absolute top-0 left-0 w-full h-full flex items-center justify-between px-3">
                          <span className="text-sm font-bold">{ratio}</span>
                          <span className="text-sm text-gray-400">
                            {/* Calculate the speed at max power RPM for this gear */}
                            {Math.round(currentVehicle.maxRPM * 0.08 / ratio / gearSettings.final)} mph
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-4">
                <h2 className="text-lg font-bold mb-4">Performance Metrics</h2>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-gray-900 p-3 rounded-lg flex flex-col items-center justify-center">
                    <BarChart2 size={24} className="text-blue-400 mb-2" />
                    <div className="text-2xl font-bold text-center">{gearSettings.topSpeed} mph</div>
                    <div className="text-xs text-gray-400 mt-1">Top Speed</div>
                  </div>
                  <div className="bg-gray-900 p-3 rounded-lg flex flex-col items-center justify-center">
                    <Clock size={24} className="text-green-400 mb-2" />
                    <div className="text-2xl font-bold text-center">{gearSettings.acceleration} sec</div>
                    <div className="text-xs text-gray-400 mt-1">0-60 mph</div>
                  </div>
                </div>
                
                <h3 className="text-gray-400 text-sm mt-4 mb-2">Engine Parameters</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  <div className="bg-gray-900 p-2 rounded-lg text-center">
                    <div className="text-xs text-gray-400 mb-1">Power</div>
                    <div className="text-lg font-bold">{currentVehicle.power} HP</div>
                  </div>
                  <div className="bg-gray-900 p-2 rounded-lg text-center">
                    <div className="text-xs text-gray-400 mb-1">Torque</div>
                    <div className="text-lg font-bold">{currentVehicle.torque} kg·m</div>
                  </div>
                  <div className="bg-gray-900 p-2 rounded-lg text-center">
                    <div className="text-xs text-gray-400 mb-1">Max RPM</div>
                    <div className="text-lg font-bold">{currentVehicle.maxRPM}</div>
                  </div>
                </div>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-4 md:col-span-2">
                <h2 className="text-lg font-bold mb-4">Gear Visualization</h2>
                <div className="h-64 w-full bg-gray-900 rounded-lg p-4 flex items-center justify-center">
                  <div className="text-center text-gray-400">
                    <div className="mb-2">Gear Visualization Graph</div>
                    <div className="text-sm">Speed vs RPM across all gears would be displayed here</div>
                  </div>
                </div>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-4 md:col-span-2">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-lg font-bold">Transmission Settings</h2>
                  <button className="px-4 py-2 bg-blue-700 hover:bg-blue-600 rounded-lg transition-colors">
                    Recalculate
                  </button>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div>
                    <label className="text-gray-400 text-sm block mb-1">Top Speed (mph)</label>
                    <input type="number" defaultValue={gearSettings.topSpeed} className="w-full bg-gray-900 text-white rounded p-2" />
                  </div>
                  <div>
                    <label className="text-gray-400 text-sm block mb-1">Min Corner Speed (mph)</label>
                    <input type="number" defaultValue="60" className="w-full bg-gray-900 text-white rounded p-2" />
                  </div>
                  <div>
                    <label className="text-gray-400 text-sm block mb-1">Tire Diameter (inches)</label>
                    <input type="number" defaultValue="26.31" className="w-full bg-gray-900 text-white rounded p-2" />
                  </div>
                  <div>
                    <label className="text-gray-400 text-sm block mb-1">Number of Gears</label>
                    <select className="w-full bg-gray-900 text-white rounded p-2">
                      <option value="4">4-Speed</option>
                      <option value="5">5-Speed</option>
                      <option value="6" selected>6-Speed</option>
                      <option value="7">7-Speed</option>
                      <option value="8">8-Speed</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {/* Saved Setups Tab */}
          {activeTab === 'saved' && (
            <div>
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-bold">Saved Setups</h2>
                <button className="px-4 py-2 bg-green-700 hover:bg-green-600 rounded-lg transition-colors flex items-center">
                  <Save size={16} className="mr-2" />
                  <span>Save Current Setup</span>
                </button>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {recentSetups.map(setup => (
                  <div key={setup.id} className="bg-gray-800 rounded-lg overflow-hidden">
                    <div className="bg-blue-900 px-4 py-2 flex justify-between items-center">
                      <div className="font-bold">{setup.name}</div>
                      <div className="text-xs text-gray-300">{setup.date}</div>
                    </div>
                    <div className="p-4">
                      <div className="text-gray-400 text-sm mb-2">{setup.vehicle}</div>
                      <p className="text-sm mb-4">{setup.notes}</p>
                      <div className="flex justify-between">
                        <button className="px-3 py-1 bg-blue-700 hover:bg-blue-600 rounded text-sm transition-colors">
                          Load
                        </button>
                        <button className="px-3 py-1 bg-red-700 hover:bg-red-600 rounded text-sm transition-colors">
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="mt-6">
                <h3 className="text-gray-400 text-sm mb-3">Setup History</h3>
                <div className="bg-gray-800 rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-gray-900">
                        <th className="text-left p-3">Name</th>
                        <th className="text-left p-3">Vehicle</th>
                        <th className="text-left p-3">Date</th>
                        <th className="text-left p-3">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {recentSetups.concat(recentSetups).map((setup, index) => (
                        <tr key={`${setup.id}-${index}`} className="border-t border-gray-700">
                          <td className="p-3">{setup.name}</td>
                          <td className="p-3">{setup.vehicle}</td>
                          <td className="p-3">{setup.date}</td>
                          <td className="p-3">
                            <div className="flex space-x-2">
                              <button className="px-2 py-1 bg-blue-800 hover:bg-blue-700 rounded text-xs transition-colors">
                                Load
                              </button>
                              <button className="px-2 py-1 bg-red-800 hover:bg-red-700 rounded text-xs transition-colors">
                                Delete
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
      
      {/* Footer */}
      <footer className="bg-gray-800 border-t border-gray-700 p-3 text-center text-gray-400 text-sm">
        GT7 Pro Tune Dashboard | Not affiliated with Polyphony Digital or Sony Interactive Entertainment
      </footer>
    </div>
  );
};

export default GT7Dashboard;
