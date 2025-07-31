#!/usr/bin/env python3
"""
SAMURAI Web Demo
A simple web-based interface for SAMURAI demonstrations
"""

import http.server
import socketserver
import os
import json
import urllib.parse
import subprocess
import threading
import time
from typing import Dict, List, Any

class SamuraiWebDemo:
    """Web-based SAMURAI demo server."""
    
    def __init__(self, port: int = 8080):
        self.port = port
        self.demo_results = {}
        
    def create_html_interface(self) -> str:
        """Create the HTML interface for the web demo."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SAMURAI Enhanced Demo</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
        }
        .container {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        h1 {
            color: #2c3e50;
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.5em;
        }
        .subtitle {
            text-align: center;
            color: #7f8c8d;
            margin-bottom: 30px;
            font-style: italic;
        }
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        .feature-card {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            border-left: 4px solid #3498db;
            transition: transform 0.3s ease;
        }
        .feature-card:hover {
            transform: translateY(-5px);
        }
        .feature-card h3 {
            color: #2c3e50;
            margin-top: 0;
        }
        .demo-section {
            margin: 30px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
        }
        .scenario-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .scenario-card {
            background: white;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .scenario-card:hover {
            box-shadow: 0 5px 20px rgba(0,0,0,0.2);
            transform: translateY(-2px);
        }
        .scenario-card.running {
            border: 2px solid #f39c12;
            background: #fff3cd;
        }
        .scenario-card.completed {
            border: 2px solid #27ae60;
            background: #d4edda;
        }
        .scenario-card.error {
            border: 2px solid #e74c3c;
            background: #f8d7da;
        }
        button {
            background: linear-gradient(45deg, #3498db, #2980b9);
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            transition: all 0.3s ease;
            margin: 5px;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(52, 152, 219, 0.4);
        }
        button:disabled {
            background: #bdc3c7;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #ecf0f1;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(45deg, #27ae60, #2ecc71);
            width: 0%;
            transition: width 0.3s ease;
        }
        .results-section {
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            display: none;
        }
        .metric-card {
            display: inline-block;
            background: white;
            padding: 15px;
            margin: 10px;
            border-radius: 8px;
            text-align: center;
            min-width: 120px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }
        .metric-label {
            color: #7f8c8d;
            font-size: 12px;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-pending { background: #f39c12; }
        .status-running { background: #3498db; animation: pulse 1s infinite; }
        .status-completed { background: #27ae60; }
        .status-error { background: #e74c3c; }
        @keyframes pulse {
            0% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.1); opacity: 0.7; }
            100% { transform: scale(1); opacity: 1; }
        }
        .log-container {
            background: #2c3e50;
            color: #ecf0f1;
            padding: 15px;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            max-height: 300px;
            overflow-y: auto;
            margin: 20px 0;
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🥷 SAMURAI</h1>
        <p class="subtitle">Adapting Segment Anything Model for Zero-Shot Visual Tracking with Motion-Aware Memory</p>
        
        <div class="features">
            <div class="feature-card">
                <h3>🎯 Zero-Shot Tracking</h3>
                <p>Track any object without training on specific targets. SAMURAI adapts to new objects instantly.</p>
            </div>
            <div class="feature-card">
                <h3>🧠 Motion-Aware Memory</h3>
                <p>Advanced memory mechanism handles occlusion and complex motion patterns robustly.</p>
            </div>
            <div class="feature-card">
                <h3>⚡ Real-Time Performance</h3>
                <p>Optimized for real-time tracking with efficient GPU utilization and memory management.</p>
            </div>
            <div class="feature-card">
                <h3>🎬 Multi-Object Support</h3>
                <p>Simultaneously track multiple objects while maintaining individual identities.</p>
            </div>
        </div>

        <div class="demo-section">
            <h2>🚀 Interactive Demo</h2>
            <p>Explore SAMURAI's capabilities through different tracking scenarios:</p>
            
            <div class="scenario-grid">
                <div class="scenario-card" id="scenario-single" onclick="runScenario('single')">
                    <div class="status-indicator status-pending" id="status-single"></div>
                    <h4>Single Object Tracking</h4>
                    <p>Track a single moving object with basic motion patterns</p>
                </div>
                <div class="scenario-card" id="scenario-multiple" onclick="runScenario('multiple')">
                    <div class="status-indicator status-pending" id="status-multiple"></div>
                    <h4>Multiple Objects</h4>
                    <p>Simultaneous tracking of multiple objects</p>
                </div>
                <div class="scenario-card" id="scenario-complex" onclick="runScenario('complex')">
                    <div class="status-indicator status-pending" id="status-complex"></div>
                    <h4>Challenging Motion</h4>
                    <p>Complex motion patterns with occlusion and scale changes</p>
                </div>
                <div class="scenario-card" id="scenario-all" onclick="runScenario('all')">
                    <div class="status-indicator status-pending" id="status-all"></div>
                    <h4>Full Benchmark</h4>
                    <p>Complete demo with performance analysis</p>
                </div>
            </div>
            
            <div style="text-align: center; margin: 20px 0;">
                <button onclick="runAllScenarios()" id="run-all-btn">🎯 Run All Scenarios</button>
                <button onclick="clearResults()" id="clear-btn">🗑️ Clear Results</button>
                <button onclick="toggleLogs()" id="logs-btn">📋 Show Logs</button>
            </div>
            
            <div class="progress-bar" id="progress-container" style="display: none;">
                <div class="progress-fill" id="progress-fill"></div>
            </div>
            
            <div class="log-container" id="log-container"></div>
        </div>

        <div class="results-section" id="results-section">
            <h2>📊 Results</h2>
            <div id="metrics-container"></div>
            <div id="detailed-results"></div>
        </div>
    </div>

    <script>
        let demoRunning = false;
        let currentScenarios = [];
        
        function log(message, type = 'info') {
            const logContainer = document.getElementById('log-container');
            const timestamp = new Date().toLocaleTimeString();
            const logEntry = document.createElement('div');
            logEntry.innerHTML = `[${timestamp}] ${message}`;
            logContainer.appendChild(logEntry);
            logContainer.scrollTop = logContainer.scrollHeight;
        }
        
        function updateStatus(scenario, status) {
            const statusElement = document.getElementById(`status-${scenario}`);
            const cardElement = document.getElementById(`scenario-${scenario}`);
            
            statusElement.className = `status-indicator status-${status}`;
            cardElement.className = `scenario-card ${status}`;
        }
        
        function updateProgress(percent) {
            const progressFill = document.getElementById('progress-fill');
            const progressContainer = document.getElementById('progress-container');
            
            if (percent > 0) {
                progressContainer.style.display = 'block';
                progressFill.style.width = percent + '%';
            } else {
                progressContainer.style.display = 'none';
            }
        }
        
        async function runScenario(scenario) {
            if (demoRunning) {
                log('⚠️ Demo already running, please wait...', 'warning');
                return;
            }
            
            demoRunning = true;
            updateStatus(scenario, 'running');
            log(`🚀 Starting ${scenario} scenario...`);
            
            try {
                const response = await fetch('/run_demo', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({scenario: scenario})
                });
                
                const result = await response.json();
                
                if (result.success) {
                    updateStatus(scenario, 'completed');
                    log(`✅ ${scenario} scenario completed successfully`);
                    displayResults(result.data);
                } else {
                    updateStatus(scenario, 'error');
                    log(`❌ ${scenario} scenario failed: ${result.error}`, 'error');
                }
            } catch (error) {
                updateStatus(scenario, 'error');
                log(`❌ Error running ${scenario}: ${error.message}`, 'error');
            }
            
            demoRunning = false;
            updateProgress(0);
        }
        
        async function runAllScenarios() {
            const scenarios = ['single', 'multiple', 'complex'];
            
            for (let i = 0; i < scenarios.length; i++) {
                await runScenario(scenarios[i]);
                updateProgress((i + 1) / scenarios.length * 100);
                await new Promise(resolve => setTimeout(resolve, 1000)); // Small delay between scenarios
            }
            
            log('🎉 All scenarios completed!');
        }
        
        function displayResults(data) {
            const resultsSection = document.getElementById('results-section');
            const metricsContainer = document.getElementById('metrics-container');
            
            resultsSection.style.display = 'block';
            
            // Clear previous results
            metricsContainer.innerHTML = '';
            
            if (data.performance) {
                const metrics = [
                    {label: 'FPS', value: data.performance.fps.toFixed(1)},
                    {label: 'Frames', value: data.performance.frames_processed},
                    {label: 'Objects', value: data.performance.objects_tracked},
                    {label: 'Quality', value: (data.summary.average_tracking_quality * 100).toFixed(1) + '%'}
                ];
                
                metrics.forEach(metric => {
                    const metricCard = document.createElement('div');
                    metricCard.className = 'metric-card';
                    metricCard.innerHTML = `
                        <div class="metric-value">${metric.value}</div>
                        <div class="metric-label">${metric.label}</div>
                    `;
                    metricsContainer.appendChild(metricCard);
                });
            }
        }
        
        function clearResults() {
            document.getElementById('results-section').style.display = 'none';
            document.getElementById('log-container').innerHTML = '';
            
            ['single', 'multiple', 'complex', 'all'].forEach(scenario => {
                updateStatus(scenario, 'pending');
            });
            
            updateProgress(0);
            log('🗑️ Results cleared');
        }
        
        function toggleLogs() {
            const logContainer = document.getElementById('log-container');
            const button = document.getElementById('logs-btn');
            
            if (logContainer.style.display === 'none' || !logContainer.style.display) {
                logContainer.style.display = 'block';
                button.textContent = '📋 Hide Logs';
            } else {
                logContainer.style.display = 'none';
                button.textContent = '📋 Show Logs';
            }
        }
        
        // Initialize
        log('🥷 SAMURAI Web Demo initialized');
        log('💡 Click on any scenario card to start tracking demonstration');
    </script>
</body>
</html>
        """
    
    def create_request_handler(self):
        """Create a custom request handler for the web demo."""
        demo_instance = self
        
        class DemoRequestHandler(http.server.SimpleHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/' or self.path == '/index.html':
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(demo_instance.create_html_interface().encode())
                else:
                    super().do_GET()
            
            def do_POST(self):
                if self.path == '/run_demo':
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))
                    
                    scenario = data.get('scenario', 'single')
                    result = demo_instance.run_demo_scenario(scenario)
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(result).encode())
                else:
                    self.send_response(404)
                    self.end_headers()
        
        return DemoRequestHandler
    
    def run_demo_scenario(self, scenario: str) -> Dict[str, Any]:
        """Run a specific demo scenario."""
        try:
            import subprocess
            import tempfile
            
            # Run the simple demo script
            result = subprocess.run([
                'python3', 'simple_demo.py', 
                '--scenario', scenario,
                '--output_dir', 'web_demo_output'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # Try to load results
                try:
                    if scenario == 'all':
                        result_file = 'web_demo_output/complete_demo_results.json'
                    else:
                        scenario_map = {
                            'single': 'single_object_tracking',
                            'multiple': 'multiple_object_tracking', 
                            'complex': 'challenging_motion_patterns'
                        }
                        result_file = f'web_demo_output/{scenario_map[scenario]}_results.json'
                    
                    if os.path.exists(result_file):
                        with open(result_file, 'r') as f:
                            data = json.load(f)
                        return {'success': True, 'data': data}
                    else:
                        return {'success': True, 'data': {'message': 'Demo completed successfully'}}
                        
                except Exception as e:
                    return {'success': True, 'data': {'message': f'Demo completed but could not load results: {e}'}}
            else:
                return {'success': False, 'error': result.stderr or 'Unknown error'}
                
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Demo timeout (30s limit exceeded)'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def run_server(self):
        """Run the web demo server."""
        handler = self.create_request_handler()
        
        try:
            with socketserver.TCPServer(("", self.port), handler) as httpd:
                print(f"🌐 SAMURAI Web Demo Server starting on port {self.port}")
                print(f"🔗 Open http://localhost:{self.port} in your browser")
                print("Press Ctrl+C to stop the server")
                httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped by user")
        except Exception as e:
            print(f"❌ Server error: {e}")

def main():
    """Main function to start the web demo."""
    import argparse
    
    parser = argparse.ArgumentParser(description="SAMURAI Web Demo Server")
    parser.add_argument("--port", type=int, default=8080, help="Server port (default: 8080)")
    args = parser.parse_args()
    
    demo = SamuraiWebDemo(port=args.port)
    demo.run_server()

if __name__ == "__main__":
    main()