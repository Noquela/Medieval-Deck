"""
Helper utilities for Medieval Deck game.

Common utility functions for file handling, logging, and data processing.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import hashlib
from datetime import datetime
import os
import shutil


def load_json(file_path: Union[str, Path], default: Any = None) -> Any:
    """
    Load JSON data from file with error handling.
    
    Args:
        file_path: Path to JSON file
        default: Default value if file doesn't exist or fails to load
        
    Returns:
        Loaded JSON data or default value
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        return default
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.warning(f"Failed to load JSON from {file_path}: {e}")
        return default


def save_json(data: Any, file_path: Union[str, Path], create_dirs: bool = True) -> bool:
    """
    Save data to JSON file with error handling.
    
    Args:
        data: Data to save
        file_path: Path to save JSON file
        create_dirs: Create parent directories if they don't exist
        
    Returns:
        True if successful, False otherwise
    """
    file_path = Path(file_path)
    
    if create_dirs:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logging.error(f"Failed to save JSON to {file_path}: {e}")
        return False


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Union[str, Path]] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Setup logging configuration.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Path to log file (optional)
        format_string: Custom format string (optional)
        
    Returns:
        Configured logger
    """
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string,
        force=True
    )
    
    # Add file handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(format_string))
        
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)
        
    return logging.getLogger("medieval_deck")


def generate_file_hash(file_path: Union[str, Path]) -> Optional[str]:
    """
    Generate MD5 hash of a file.
    
    Args:
        file_path: Path to file
        
    Returns:
        MD5 hash string or None if file doesn't exist
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        return None
        
    try:
        with open(file_path, 'rb') as f:
            file_hash = hashlib.md5()
            for chunk in iter(lambda: f.read(4096), b""):
                file_hash.update(chunk)
        return file_hash.hexdigest()
    except Exception as e:
        logging.warning(f"Failed to generate hash for {file_path}: {e}")
        return None


def ensure_directory(dir_path: Union[str, Path]) -> bool:
    """
    Ensure directory exists, create if necessary.
    
    Args:
        dir_path: Path to directory
        
    Returns:
        True if directory exists or was created successfully
    """
    dir_path = Path(dir_path)
    
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logging.error(f"Failed to create directory {dir_path}: {e}")
        return False


def clean_filename(filename: str) -> str:
    """
    Clean filename by removing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Cleaned filename safe for filesystem
    """
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    cleaned = filename
    
    for char in invalid_chars:
        cleaned = cleaned.replace(char, '_')
        
    # Remove leading/trailing whitespace and dots
    cleaned = cleaned.strip(' .')
    
    # Ensure filename is not empty
    if not cleaned:
        cleaned = "unnamed"
        
    return cleaned


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def get_file_info(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Get comprehensive file information.
    
    Args:
        file_path: Path to file
        
    Returns:
        Dictionary with file information
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        return {"exists": False}
        
    try:
        stat = file_path.stat()
        
        return {
            "exists": True,
            "name": file_path.name,
            "stem": file_path.stem,
            "suffix": file_path.suffix,
            "size_bytes": stat.st_size,
            "size_formatted": format_file_size(stat.st_size),
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "is_file": file_path.is_file(),
            "is_dir": file_path.is_dir(),
            "absolute_path": str(file_path.absolute()),
            "hash": generate_file_hash(file_path)
        }
    except Exception as e:
        logging.warning(f"Failed to get file info for {file_path}: {e}")
        return {"exists": True, "error": str(e)}


def backup_file(file_path: Union[str, Path], backup_dir: Optional[Union[str, Path]] = None) -> Optional[Path]:
    """
    Create backup of a file.
    
    Args:
        file_path: Path to file to backup
        backup_dir: Directory to store backup (optional)
        
    Returns:
        Path to backup file or None if failed
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        return None
        
    if backup_dir is None:
        backup_dir = file_path.parent / "backups"
    else:
        backup_dir = Path(backup_dir)
        
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
    backup_path = backup_dir / backup_name
    
    try:
        shutil.copy2(file_path, backup_path)
        logging.info(f"Created backup: {backup_path}")
        return backup_path
    except Exception as e:
        logging.error(f"Failed to create backup of {file_path}: {e}")
        return None


def find_files(
    directory: Union[str, Path],
    pattern: str = "*",
    recursive: bool = True,
    include_dirs: bool = False
) -> List[Path]:
    """
    Find files matching pattern in directory.
    
    Args:
        directory: Directory to search
        pattern: Glob pattern to match
        recursive: Search recursively
        include_dirs: Include directories in results
        
    Returns:
        List of matching file paths
    """
    directory = Path(directory)
    
    if not directory.exists():
        return []
        
    try:
        if recursive:
            glob_pattern = f"**/{pattern}"
            files = directory.glob(glob_pattern)
        else:
            files = directory.glob(pattern)
            
        result = []
        for file_path in files:
            if include_dirs or file_path.is_file():
                result.append(file_path)
                
        return sorted(result)
    except Exception as e:
        logging.warning(f"Failed to find files in {directory}: {e}")
        return []


def delete_old_files(
    directory: Union[str, Path],
    max_age_days: int,
    pattern: str = "*",
    dry_run: bool = False
) -> List[Path]:
    """
    Delete files older than specified age.
    
    Args:
        directory: Directory to clean
        max_age_days: Maximum age in days
        pattern: File pattern to match
        dry_run: If True, only return files that would be deleted
        
    Returns:
        List of deleted (or would-be-deleted) files
    """
    directory = Path(directory)
    
    if not directory.exists():
        return []
        
    cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 60 * 60)
    deleted_files = []
    
    try:
        for file_path in directory.glob(pattern):
            if file_path.is_file():
                file_time = file_path.stat().st_mtime
                
                if file_time < cutoff_time:
                    if not dry_run:
                        file_path.unlink()
                        logging.info(f"Deleted old file: {file_path}")
                    deleted_files.append(file_path)
                    
    except Exception as e:
        logging.error(f"Failed to clean old files in {directory}: {e}")
        
    return deleted_files


def validate_json_schema(data: Any, required_fields: List[str]) -> List[str]:
    """
    Validate JSON data against required fields.
    
    Args:
        data: Data to validate
        required_fields: List of required field names
        
    Returns:
        List of missing fields
    """
    if not isinstance(data, dict):
        return required_fields
        
    missing_fields = []
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
            
    return missing_fields


def merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two configuration dictionaries.
    
    Args:
        base_config: Base configuration
        override_config: Configuration to merge in
        
    Returns:
        Merged configuration
    """
    merged = base_config.copy()
    
    for key, value in override_config.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = merge_configs(merged[key], value)
        else:
            merged[key] = value
            
    return merged


def get_system_info() -> Dict[str, Any]:
    """
    Get system information for debugging.
    
    Returns:
        Dictionary with system information
    """
    import platform
    import sys
    
    info = {
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": sys.version,
        "python_executable": sys.executable,
        "working_directory": os.getcwd(),
    }
    
    # Add memory info if available
    try:
        import psutil
        memory = psutil.virtual_memory()
        info["memory"] = {
            "total_gb": memory.total / 1024**3,
            "available_gb": memory.available / 1024**3,
            "percent_used": memory.percent
        }
    except ImportError:
        pass
        
    # Add GPU info if available
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name()
            major, minor = torch.cuda.get_device_capability(0)
            cuda_capability = f"sm_{major}{minor}"
            
            info["cuda"] = {
                "available": True,
                "device_count": torch.cuda.device_count(),
                "current_device": torch.cuda.current_device(),
                "device_name": gpu_name,
                "cuda_capability": cuda_capability,
                "memory_gb": torch.cuda.get_device_properties(0).total_memory / 1024**3
            }
            
            # Check for RTX 50 series compatibility
            rtx_50_series = ["RTX 5070", "RTX 5070 Ti", "RTX 5080", "RTX 5090"]
            is_rtx_50 = any(gpu in gpu_name for gpu in rtx_50_series)
            
            # Check if PyTorch version supports sm_120 (CUDA 12.8+)
            import torch
            torch_version = torch.__version__
            has_cu128 = "+cu128" in torch_version
            requires_nightly = is_rtx_50 and cuda_capability == "sm_120" and not has_cu128
            
            info["cuda"]["is_rtx_50_series"] = is_rtx_50
            info["cuda"]["requires_pytorch_nightly"] = requires_nightly
            info["cuda"]["pytorch_version"] = torch_version
            
            if requires_nightly:
                info["cuda"]["compatibility_note"] = "RTX 50 series detected - requires PyTorch with CUDA 12.8"
            elif is_rtx_50 and has_cu128:
                info["cuda"]["compatibility_note"] = "RTX 50 series fully supported with CUDA 12.8"
        else:
            info["cuda"] = {"available": False}
    except ImportError:
        info["cuda"] = {"available": False, "error": "PyTorch not installed"}
    except Exception as e:
        info["cuda"] = {"available": False, "error": str(e)}
        
    return info
