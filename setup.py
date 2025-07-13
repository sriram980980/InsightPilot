from setuptools import setup, find_packages

setup(
    name="insightpilot",
    version="1.0.0",
    description="AI-powered desktop application for data exploration and analysis",
    author="InsightPilot Team",
    author_email="team@insightpilot.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "PySide6>=6.5.0",
        "requests>=2.31.0",
        "keyring>=24.2.0",
        "cryptography>=41.0.0",
        "grpcio>=1.57.0",
        "grpcio-tools>=1.57.0",
        "protobuf>=4.24.0",
        "mysql-connector-python>=8.1.0",
        "oracledb>=1.4.0",
        "pymongo>=4.5.0",
        "matplotlib>=3.7.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-qt>=4.2.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "insightpilot=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
