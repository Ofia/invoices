#!/bin/bash
# Environment setup script for Invoice Management project
# Run this with: source setup_env.sh

echo "Setting up Invoice Management environment..."

# Add PostgreSQL to PATH
# Automatically detect PostgreSQL version
PG_PATH=""
for version in 18 17 16 15; do
    if [ -d "/c/Program Files/PostgreSQL/$version/bin" ]; then
        PG_PATH="/c/Program Files/PostgreSQL/$version/bin"
        echo "✓ Found PostgreSQL $version"
        break
    fi
done

if [ -n "$PG_PATH" ]; then
    export PATH=$PATH:"$PG_PATH"
    echo "✓ PostgreSQL added to PATH"
    psql --version
else
    echo "⚠ PostgreSQL not found in standard locations"
    echo "  If you have PostgreSQL installed, add it manually:"
    echo "  export PATH=\$PATH:\"/c/Program Files/PostgreSQL/YOUR_VERSION/bin\""
fi

echo ""
echo "Environment ready! You can now use:"
echo "  - psql (PostgreSQL commands)"
echo "  - alembic (Database migrations)"
echo "  - uvicorn (Start the server)"
echo ""
echo "Quick commands:"
echo "  cd backend"
echo "  ./venv/Scripts/alembic.exe upgrade head"
echo "  ./venv/Scripts/uvicorn.exe app.main:app --reload"
