"""
GPU Compatibility Detection and Auto-Fix for RTX 50 Series

Automatically detects RTX 5070/5070 Ti compatibility issues and installs
PyTorch nightly when needed.
"""

import subprocess
import sys
import logging
import re
import warnings
from typing import Optional, Tuple, List
from pathlib import Path
import importlib.util

logger = logging.getLogger(__name__)


class GPUCompatibilityManager:
    """Manages GPU compatibility and PyTorch version detection."""
    
    # CUDA capabilities for RTX 50 series (sm_120)
    RTX_50_SERIES_GPUS = [
        "RTX 5070",
        "RTX 5070 Ti", 
        "RTX 5080",
        "RTX 5090"
    ]
    
    # CUDA capability that requires nightly PyTorch
    RTX_50_CUDA_CAPABILITY = "sm_120"
    
    def __init__(self):
        self.gpu_name: Optional[str] = None
        self.cuda_capability: Optional[str] = None
        self.pytorch_supports_gpu: bool = False
        self.needs_nightly: bool = False
        self.torch_available: bool = False
        
    def _safe_import_torch(self) -> bool:
        """
        Safely import torch and check if it's available.
        
        Returns:
            True if torch is available, False otherwise
        """
        try:
            import torch
            self.torch_available = True
            return True
        except ImportError:
            self.torch_available = False
            logger.warning("PyTorch not found, will attempt to install")
            return False
        except Exception as e:
            logger.error(f"Error importing PyTorch: {e}")
            self.torch_available = False
            return False
    
    def detect_gpu_info(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Detect GPU name and CUDA capability.
        
        Returns:
            Tuple of (gpu_name, cuda_capability)
        """
        if not self._safe_import_torch():
            return None, None
            
        try:
            import torch
            
            if torch.cuda.is_available():
                self.gpu_name = torch.cuda.get_device_name(0)
                
                # Get CUDA capability
                major, minor = torch.cuda.get_device_capability(0)
                self.cuda_capability = f"sm_{major}{minor}"
                
                logger.info(f"Detected GPU: {self.gpu_name}")
                logger.info(f"CUDA Capability: {self.cuda_capability}")
                
                return self.gpu_name, self.cuda_capability
            else:
                logger.warning("CUDA not available")
                return None, None
                
        except Exception as e:
            logger.error(f"Error detecting GPU info: {e}")
            return None, None
    
    def is_rtx_50_series(self) -> bool:
        """
        Check if the detected GPU is from RTX 50 series.
        
        Returns:
            True if RTX 50 series GPU detected
        """
        if not self.gpu_name:
            return False
            
        return any(gpu in self.gpu_name for gpu in self.RTX_50_SERIES_GPUS)
    
    def check_pytorch_compatibility(self) -> bool:
        """
        Check if current PyTorch installation supports the detected GPU.
        
        Returns:
            True if compatible, False if needs upgrade
        """
        if not self._safe_import_torch():
            return False
            
        # Detect GPU info if not already done
        if not self.gpu_name:
            self.detect_gpu_info()
        
        # If no GPU or not RTX 50 series, assume compatible
        if not self.is_rtx_50_series():
            self.pytorch_supports_gpu = True
            return True
        
        # Check for the specific CUDA capability warning
        try:
            import torch
            
            # Capture warnings to detect compatibility issues
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                
                # Trigger CUDA initialization to check compatibility
                if torch.cuda.is_available():
                    _ = torch.cuda.device_count()
                    _ = torch.cuda.get_device_name(0)
                
                # Check if we got the sm_120 compatibility warning
                for warning in w:
                    warning_msg = str(warning.message)
                    if "sm_120" in warning_msg and "not compatible" in warning_msg:
                        logger.warning("Detected RTX 50 series compatibility issue")
                        self.needs_nightly = True
                        self.pytorch_supports_gpu = False
                        return False
            
            # If we reach here, no compatibility warning was detected
            self.pytorch_supports_gpu = True
            return True
            
        except Exception as e:
            logger.error(f"Error checking PyTorch compatibility: {e}")
            return False
    
    def get_python_executable(self) -> str:
        """
        Get the Python executable path for the current environment.
        
        Returns:
            Path to Python executable
        """
        return sys.executable
    
    def install_pytorch_stable_cu128(self) -> bool:
        """
        Install stable PyTorch 2.7.x with CUDA 12.8 support for RTX 50 series.
        
        Returns:
            True if installation successful, False otherwise
        """
        logger.info("Installing PyTorch 2.7.x with CUDA 12.8 for RTX 50 series support...")
        logger.info("This may take several minutes and download ~3GB of data...")
        
        python_exe = self.get_python_executable()
        
        # Commands to run
        uninstall_cmd = [
            python_exe, "-m", "pip", "uninstall", 
            "torch", "torchvision", "torchaudio", "-y"
        ]
        
        install_cmd_stable = [
            python_exe, "-m", "pip", "install",
            "torch==2.7.1+cu128", "torchvision==0.14.1+cu128", "torchaudio==2.7.1+cu128",
            "--extra-index-url", "https://download.pytorch.org/whl/cu128"
        ]
        
        install_cmd_nightly = [
            python_exe, "-m", "pip", "install", "--pre",
            "torch", "torchvision", "torchaudio",
            "--index-url", "https://download.pytorch.org/whl/nightly/cu128"
        ]
        
        try:
            # Uninstall current PyTorch
            logger.info("Uninstalling current PyTorch...")
            result = subprocess.run(
                uninstall_cmd,
                capture_output=True,
                text=True,
                check=True
            )
            logger.debug(f"Uninstall output: {result.stdout}")
            
            # Try stable version first
            logger.info("Attempting to install stable PyTorch 2.7.x with CUDA 12.8...")
            try:
                result = subprocess.run(
                    install_cmd_stable,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=600  # 10 minutes timeout
                )
                logger.debug(f"Stable install output: {result.stdout}")
                logger.info("Stable PyTorch 2.7.x with CUDA 12.8 installed successfully!")
                return True
                
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                logger.warning("Stable version failed, trying nightly...")
                logger.debug(f"Stable install error: {e}")
                
                # Fallback to nightly
                logger.info("Installing PyTorch nightly with CUDA 12.8...")
                result = subprocess.run(
                    install_cmd_nightly,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=600  # 10 minutes timeout
                )
                logger.debug(f"Nightly install output: {result.stdout}")
                logger.info("PyTorch nightly with CUDA 12.8 installed successfully!")
                return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install PyTorch with CUDA 12.8: {e}")
            logger.error(f"Command output: {e.stdout}")
            logger.error(f"Command error: {e.stderr}")
            return False
        except subprocess.TimeoutExpired:
            logger.error("PyTorch installation timed out after 10 minutes")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during PyTorch installation: {e}")
            return False

    def install_pytorch_nightly(self) -> bool:
        """
        Install PyTorch nightly with CUDA 12.8 support for RTX 50 series.
        
        Returns:
            True if installation successful, False otherwise
        """
        # Use the combined stable+nightly approach
        return self.install_pytorch_stable_cu128()
    
    def auto_fix_compatibility(self, interactive: bool = True) -> bool:
        """
        Automatically fix GPU compatibility issues.
        
        Args:
            interactive: If True, ask user for confirmation before installing
            
        Returns:
            True if fix was successful or not needed, False if failed
        """
        # Check if we need to fix anything
        if self.check_pytorch_compatibility():
            logger.info("PyTorch is compatible with your GPU")
            return True
        
        if not self.needs_nightly:
            logger.info("No PyTorch nightly installation needed")
            return True
        
        # We need to install nightly PyTorch
        logger.warning(f"Detected {self.gpu_name} with CUDA capability {self.cuda_capability}")
        logger.warning("Current PyTorch installation is not compatible")
        
        if interactive:
            print("\n" + "="*60)
            print("🔧 GPU COMPATIBILITY ISSUE DETECTED")
            print("="*60)
            print(f"GPU: {self.gpu_name}")
            print(f"CUDA Capability: {self.cuda_capability}")
            print("\nYour RTX 50 series GPU requires PyTorch with CUDA 12.8 for proper support.")
            print("This will:")
            print("  • Uninstall current PyTorch")
            print("  • Try stable PyTorch 2.7.x+cu128 first")
            print("  • Fallback to nightly PyTorch+cu128 if needed")
            print("  • Download ~3GB of PyTorch binaries")
            print("  • Enable full RTX 50 series CUDA acceleration")
            print("\nThis is a one-time setup that will resolve the sm_120 compatibility issue.")
            
            response = input("\nProceed with automatic fix? (y/N): ").strip().lower()
            if response not in ['y', 'yes']:
                print("Skipping automatic fix. GPU acceleration may not work properly.")
                return False
        
        # Perform the fix
        success = self.install_pytorch_nightly()
        
        if success:
            print("\n✅ GPU compatibility fix completed successfully!")
            print("Please restart the application to use the updated PyTorch.")
            
            # Suggest restart
            if interactive:
                input("\nPress Enter to exit (restart required)...")
            sys.exit(0)
        else:
            print("\n❌ Failed to fix GPU compatibility automatically.")
            print("You may need to install PyTorch with CUDA 12.8 manually:")
            print("Option 1 (Stable):")
            print("pip uninstall torch torchvision torchaudio")
            print("pip install torch==2.7.1+cu128 torchvision==0.14.1+cu128 torchaudio==2.7.1+cu128 \\")
            print("  --extra-index-url https://download.pytorch.org/whl/cu128")
            print("Option 2 (Nightly):")
            print("pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128")
            return False
    
    def run_compatibility_check(self, auto_fix: bool = True, interactive: bool = True) -> bool:
        """
        Run complete compatibility check and optional auto-fix.
        
        Args:
            auto_fix: Whether to automatically fix issues
            interactive: Whether to ask for user confirmation
            
        Returns:
            True if system is compatible, False otherwise
        """
        logger.info("Running GPU compatibility check...")
        
        # Detect GPU
        self.detect_gpu_info()
        
        # Check compatibility
        is_compatible = self.check_pytorch_compatibility()
        
        if is_compatible:
            logger.info("✅ GPU compatibility check passed")
            return True
        
        if auto_fix:
            return self.auto_fix_compatibility(interactive)
        else:
            logger.warning("❌ GPU compatibility issues detected, but auto-fix disabled")
            return False


def check_and_fix_gpu_compatibility(auto_fix: bool = True, interactive: bool = True) -> bool:
    """
    Convenience function to check and fix GPU compatibility.
    
    Args:
        auto_fix: Whether to automatically fix issues
        interactive: Whether to ask for user confirmation
        
    Returns:
        True if system is compatible, False otherwise
    """
    manager = GPUCompatibilityManager()
    return manager.run_compatibility_check(auto_fix, interactive)
