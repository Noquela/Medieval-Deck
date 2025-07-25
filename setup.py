from setuptools import setup, find_packages

setup(
    name="medieval-deck",
    version="1.0.0",
    description="Medieval Deck Card Game with AI-Generated Backgrounds",
    author="Bruno",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.13",
    install_requires=[
        "torch>=2.1.0",
        "diffusers>=0.24.0",
        "transformers>=4.35.0",
        "accelerate>=0.24.0",
        "pygame>=2.5.0",
        "pillow>=10.0.0",
        "opencv-python>=4.8.0",
        "numpy>=1.24.0",
        "requests>=2.31.0",
        "tqdm>=4.66.0",
        "safetensors>=0.4.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
        "upscaling": [
            "realesrgan",
        ],
    },
    entry_points={
        "console_scripts": [
            "medieval-deck=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Programming Language :: Python :: 3.13",
        "Topic :: Games/Entertainment :: Board Games",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
