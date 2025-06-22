from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="claude-usage-tracker",
    version="1.0.0",
    author="Bo Wu",
    author_email="",
    description="Track Claude Code usage and costs with beautiful ASCII charts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/claude-usage-tracker",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        # Core tool has no dependencies!
    ],
    extras_require={
        "menubar": ["rumps>=0.4.0"],  # For macOS menu bar widget
        "dev": [
            "pytest>=6.0",
            "black>=22.0",
            "flake8>=4.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "claude-usage-tracker=claude_usage_tracker:main",
            "cu=claude_usage_tracker:main",
        ],
    },
    scripts=[
        "claude-usage",
        "claude_tmux_status.sh",
        "start_menu_bar.sh",
    ],
)