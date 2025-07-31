#!/usr/bin/env python3
"""
SAMURAI Installation and Environment Setup Script
Automated setup and optimization for SAMURAI demo environment.
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path
import json
import time

class SamuraiSetup:
    """Automated setup and optimization for SAMURAI environment."""
    
    def __init__(self):
        self.system_info = self._get_system_info()
        self.setup_log = []
        
    def _get_system_info(self) -> dict:
        """Get system information for optimization."""
        return {
            "platform": platform.platform(),
            "python_version": sys.version,
            "cpu_count": os.cpu_count(),
            "has_gpu": self._check_gpu_availability(),
            "memory_gb": self._get_memory_info(),
            "disk_space_gb": self._get_disk_space()
        }
    
    def _check_gpu_availability(self) -> bool:
        """Check if CUDA GPU is available."""
        try:
            result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def _get_memory_info(self) -> float:
        """Get system memory information (GB)."""
        try:
            import psutil
            return psutil.virtual_memory().total / (1024**3)
        except ImportError:
            return 8.0  # Default assumption
    
    def _get_disk_space(self) -> float:
        """Get available disk space (GB)."""
        try:
            import shutil
            total, used, free = shutil.disk_usage(".")
            return free / (1024**3)
        except:
            return 10.0  # Default assumption
    
    def log(self, message: str, status: str = "INFO"):
        """Log setup messages."""
        timestamp = time.strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {status}: {message}"
        self.setup_log.append(log_entry)
        
        # Color coding for console output
        colors = {
            "INFO": "\033[94m",    # Blue
            "SUCCESS": "\033[92m", # Green
            "WARNING": "\033[93m", # Yellow
            "ERROR": "\033[91m",   # Red
            "RESET": "\033[0m"     # Reset
        }
        
        color = colors.get(status, colors["INFO"])
        print(f"{color}{log_entry}{colors['RESET']}")
    
    def check_python_environment(self) -> bool:
        """Check Python environment compatibility."""
        self.log("Checking Python environment...")
        
        # Check Python version
        python_version = sys.version_info
        if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
            self.log(f"Python {python_version.major}.{python_version.minor} detected. Python 3.8+ recommended.", "WARNING")
            return False
        else:
            self.log(f"Python {python_version.major}.{python_version.minor} is compatible", "SUCCESS")
            return True
    
    def install_basic_dependencies(self) -> bool:
        """Install basic dependencies for demos."""
        self.log("Installing basic dependencies...")
        
        basic_packages = ["numpy", "Pillow"]
        
        for package in basic_packages:
            try:
                self.log(f"Installing {package}...")
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", package
                ], capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0:
                    try:
                        __import__(package)
                        self.log(f"{package} installed and importable", "SUCCESS")
                    except ImportError:
                        self.log(f"{package} installed but not importable", "WARNING")
                else:
                    self.log(f"Failed to install {package}: {result.stderr}", "WARNING")
                    
            except subprocess.TimeoutExpired:
                self.log(f"Timeout installing {package}", "WARNING")
            except Exception as e:
                self.log(f"Error installing {package}: {e}", "WARNING")
        
        return True
    
    def setup_enhanced_demos(self) -> bool:
        """Set up the enhanced demo environment."""
        self.log("Setting up enhanced demo environment...")
        
        # Create output directories
        demo_dirs = [
            "demo_output",
            "benchmark_results", 
            "web_demo_output",
            "sample_data"
        ]
        
        for dir_name in demo_dirs:
            try:
                os.makedirs(dir_name, exist_ok=True)
                self.log(f"Created directory: {dir_name}", "SUCCESS")
            except Exception as e:
                self.log(f"Failed to create directory {dir_name}: {e}", "ERROR")
                return False
        
        return True
    
    def optimize_for_system(self) -> dict:
        """Generate optimized configuration for the current system."""
        self.log("Generating system-optimized configuration...")
        
        config = {
            "performance_mode": "balanced",
            "recommended_scenarios": [],
            "memory_settings": {},
            "processing_settings": {}
        }
        
        # Performance mode based on hardware
        if self.system_info["has_gpu"] and self.system_info["memory_gb"] >= 8:
            config["performance_mode"] = "high_performance"
            config["recommended_scenarios"] = ["all"]
            self.log("High performance mode recommended", "SUCCESS")
        elif self.system_info["memory_gb"] >= 4:
            config["performance_mode"] = "balanced"
            config["recommended_scenarios"] = ["single", "multiple"]
            self.log("Balanced performance mode recommended", "INFO")
        else:
            config["performance_mode"] = "lightweight"
            config["recommended_scenarios"] = ["single"]
            self.log("Lightweight mode recommended for system", "WARNING")
        
        # Memory settings
        config["memory_settings"] = {
            "max_frames_in_memory": min(100, int(self.system_info["memory_gb"] * 10)),
            "enable_memory_optimization": self.system_info["memory_gb"] < 8,
            "use_frame_caching": self.system_info["memory_gb"] >= 4
        }
        
        # Processing settings
        config["processing_settings"] = {
            "parallel_processing": self.system_info["cpu_count"] >= 4,
            "max_workers": min(4, self.system_info["cpu_count"]),
            "enable_gpu_acceleration": self.system_info["has_gpu"],
            "frame_skip_ratio": 1 if self.system_info["has_gpu"] else 2
        }
        
        return config
    
    def create_demo_launcher(self, config: dict):
        """Create optimized demo launcher script."""
        self.log("Creating optimized demo launcher...")
        
        launcher_content = f'''#!/usr/bin/env python3
"""
Optimized SAMURAI Demo Launcher
Auto-generated for your system configuration.
"""

import sys
import os

# System configuration
SYSTEM_CONFIG = {json.dumps(config, indent=4)}

def main():
    """Launch demos with optimized settings."""
    print("🥷 SAMURAI Enhanced Demo Launcher")
    print(f"🖥️  Performance Mode: {{SYSTEM_CONFIG['performance_mode']}}")
    print(f"🎯 Recommended Scenarios: {{', '.join(SYSTEM_CONFIG['recommended_scenarios'])}}")
    print()
    
    while True:
        print("Available demos:")
        print("1. 🎯 Simple Interactive Demo")
        print("2. 🌐 Web Interface Demo") 
        print("3. 📊 Performance Benchmark")
        print("4. 🚀 Run Recommended Scenarios")
        print("5. ❌ Exit")
        
        choice = input("\\nSelect demo (1-5): ").strip()
        
        if choice == "1":
            os.system("python simple_demo.py")
        elif choice == "2":
            print("Starting web demo on http://localhost:8080")
            os.system("python web_demo.py")
        elif choice == "3":
            runs = 1 if SYSTEM_CONFIG['performance_mode'] == 'lightweight' else 3
            os.system(f"python benchmark_suite.py --runs {{runs}}")
        elif choice == "4":
            for scenario in SYSTEM_CONFIG['recommended_scenarios']:
                print(f"Running {{scenario}} scenario...")
                os.system(f"python simple_demo.py --scenario {{scenario}}")
        elif choice == "5":
            print("👋 Goodbye!")
            break
        else:
            print("Invalid choice. Please select 1-5.")

if __name__ == "__main__":
    main()
'''
        
        try:
            with open("launch_demos.py", "w") as f:
                f.write(launcher_content)
            
            # Make executable on Unix systems
            if platform.system() != "Windows":
                os.chmod("launch_demos.py", 0o755)
            
            self.log("Demo launcher created: launch_demos.py", "SUCCESS")
            
        except Exception as e:
            self.log(f"Failed to create launcher: {e}", "ERROR")
    
    def run_quick_test(self) -> bool:
        """Run a quick test to verify setup."""
        self.log("Running quick functionality test...")
        
        try:
            # Test simple demo
            result = subprocess.run([
                sys.executable, "simple_demo.py", "--scenario", "single"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.log("Simple demo test passed", "SUCCESS")
                return True
            else:
                self.log(f"Simple demo test failed: {result.stderr}", "ERROR")
                return False
                
        except subprocess.TimeoutExpired:
            self.log("Test timeout - this may indicate performance issues", "WARNING")
            return False
        except Exception as e:
            self.log(f"Test error: {e}", "ERROR")
            return False
    
    def generate_setup_report(self, config: dict, test_passed: bool):
        """Generate comprehensive setup report."""
        self.log("Generating setup report...")
        
        report = {
            "setup_timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "system_info": self.system_info,
            "configuration": config,
            "test_results": {"basic_functionality": test_passed},
            "setup_log": self.setup_log,
            "next_steps": []
        }
        
        # Add next steps based on setup results
        if test_passed:
            report["next_steps"] = [
                "Run 'python launch_demos.py' to start the demo launcher",
                "Try 'python web_demo.py' for the web interface",
                "Use 'python benchmark_suite.py' for performance testing"
            ]
        else:
            report["next_steps"] = [
                "Check the setup log for any error messages",
                "Ensure Python 3.8+ is installed",
                "Try running demos individually for debugging"
            ]
        
        # Save report
        try:
            with open("setup_report.json", "w") as f:
                json.dump(report, f, indent=2)
            
            # Create human-readable version
            with open("SETUP_REPORT.txt", "w") as f:
                f.write("SAMURAI Enhanced Demo Setup Report\\n")
                f.write("=" * 50 + "\\n\\n")
                f.write(f"Setup Date: {report['setup_timestamp']}\\n")
                f.write(f"System: {self.system_info['platform']}\\n")
                f.write(f"Python: {self.system_info['python_version'].split()[0]}\\n")
                f.write(f"Performance Mode: {config['performance_mode']}\\n")
                f.write(f"Basic Test: {'PASSED' if test_passed else 'FAILED'}\\n\\n")
                
                f.write("Next Steps:\\n")
                for i, step in enumerate(report["next_steps"], 1):
                    f.write(f"{i}. {step}\\n")
            
            self.log("Setup report saved: SETUP_REPORT.txt", "SUCCESS")
            
        except Exception as e:
            self.log(f"Failed to save setup report: {e}", "ERROR")
    
    def run_full_setup(self) -> bool:
        """Run the complete setup process."""
        print("🥷 SAMURAI Enhanced Demo Setup")
        print("=" * 40)
        
        # Check environment
        if not self.check_python_environment():
            self.log("Environment check failed", "ERROR")
            return False
        
        # Install basic dependencies
        self.install_basic_dependencies()
        
        # Setup demo environment
        if not self.setup_enhanced_demos():
            self.log("Demo setup failed", "ERROR")
            return False
        
        # Generate optimized configuration
        config = self.optimize_for_system()
        
        # Create launcher
        self.create_demo_launcher(config)
        
        # Run quick test
        test_passed = self.run_quick_test()
        
        # Generate report
        self.generate_setup_report(config, test_passed)
        
        # Final summary
        print("\\n" + "=" * 40)
        if test_passed:
            self.log("🎉 Setup completed successfully!", "SUCCESS")
            print("\\n🚀 Ready to run SAMURAI demos!")
            print("📋 Check SETUP_REPORT.txt for details")
            print("🎯 Run 'python launch_demos.py' to get started")
        else:
            self.log("⚠️ Setup completed with warnings", "WARNING")
            print("\\n🔧 Some issues detected - check SETUP_REPORT.txt")
            print("🎯 You can still try running demos individually")
        
        return test_passed

def main():
    """Main setup function."""
    setup = SamuraiSetup()
    success = setup.run_full_setup()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())