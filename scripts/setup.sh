#!/bin/bash

# ========================================
# 🚀 PandasPlayground Setup Script
# ========================================
# Automated setup for development environment

set -e  # Exit on error

echo "📊 Setting up PandasPlayground..."
echo ""

# Check Python version
echo "🐍 Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then 
    echo "❌ Python 3.9 or higher required. Found: Python $python_version"
    exit 1
fi
echo "✅ Python $python_version detected"
echo ""

# Create virtual environment
echo "🔧 Creating virtual environment..."
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists. Skipping creation."
else
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi
echo ""

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
python -m pip install --upgrade pip -q
echo "✅ pip upgraded"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
echo "   This may take a few minutes..."
pip install -r requirements.txt -q
echo "✅ Dependencies installed"
echo ""

# Create necessary directories
echo "📁 Creating project directories..."
mkdir -p exports
mkdir -p assets
mkdir -p docs
echo "✅ Directories created"
echo ""

# Run tests to verify installation
echo "🧪 Running tests to verify installation..."
if python -m pytest scripts/test_utils.py -v; then
    echo "✅ Tests passed"
else
    echo "⚠️  Some tests failed, but installation is complete"
fi
echo ""

# Display success message
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✨ Setup complete! ✨"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 Next steps:"
echo "   1. Activate virtual environment:"
echo "      source venv/bin/activate"
echo ""
echo "   2. Start Jupyter Lab:"
echo "      make run-jupyter"
echo "      (or: jupyter lab)"
echo ""
echo "   3. Start Streamlit dashboard:"
echo "      make run-streamlit"
echo "      (or: streamlit run STREAMLIT_App.py)"
echo ""
echo "   4. Run tests:"
echo "      make test"
echo "      (or: pytest -v)"
echo ""
echo "🎓 Happy learning with PandasPlayground!"
echo ""
