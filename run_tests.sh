#!/bin/bash

# Export necessary environment variables
export SECRET_KEY=testsecretkey
export ALGORITHM=HS256
export ACCESS_TOKEN_EXPIRE_MINUTES=30

# Check if we should skip dependency installation
if [ "$1" != "--skip-install" ]; then
  echo "Installing dependencies... (use --skip-install to skip this step)"
  pip install -r test-requirements.txt
else
  echo "Skipping dependency installation..."
fi

# Create necessary directories for testing
mkdir -p tests
touch tests/__init__.py
touch __init__.py

# Run the tests from the project root
python -m pytest tests/ --cov=app -v