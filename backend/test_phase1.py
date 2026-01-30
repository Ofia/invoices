"""
Phase 1 Testing Script

This script tests the backend foundation to ensure everything is set up correctly.
Run this after setting up PostgreSQL and running migrations.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all modules can be imported"""
    print("🔍 Testing imports...")
    try:
        from app.core.config import settings
        from app.core.database import Base, engine, get_db
        from app.models import User, Workspace, Supplier, Invoice, PendingDocument, ProcessedEmail
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def test_database_connection():
    """Test database connection"""
    print("\n🔍 Testing database connection...")
    try:
        from app.core.database import engine
        from sqlalchemy import text

        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()

        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Is PostgreSQL running? Check services.msc")
        print("2. Is DATABASE_URL correct in .env?")
        print("3. Does the database exist? Run: psql -U postgres -l")
        return False


def test_tables_exist():
    """Test that all tables exist"""
    print("\n🔍 Testing database tables...")
    try:
        from app.core.database import Base, engine
        from sqlalchemy import inspect

        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()

        expected_tables = [
            'users',
            'workspaces',
            'suppliers',
            'invoices',
            'pending_documents',
            'processed_emails'
        ]

        missing_tables = [t for t in expected_tables if t not in existing_tables]

        if missing_tables:
            print(f"❌ Missing tables: {', '.join(missing_tables)}")
            print("\nRun migrations with: alembic upgrade head")
            return False

        print(f"✅ All {len(expected_tables)} tables exist")
        for table in expected_tables:
            print(f"   - {table}")
        return True
    except Exception as e:
        print(f"❌ Table check failed: {e}")
        return False


def test_table_structure():
    """Test table structure and relationships"""
    print("\n🔍 Testing table structure...")
    try:
        from app.core.database import engine
        from sqlalchemy import inspect

        inspector = inspect(engine)

        # Test users table
        users_columns = [col['name'] for col in inspector.get_columns('users')]
        required_users_cols = ['id', 'email', 'google_id', 'oauth_token', 'created_at']
        if not all(col in users_columns for col in required_users_cols):
            print("❌ Users table structure incorrect")
            return False

        # Test foreign keys
        invoices_fks = inspector.get_foreign_keys('invoices')
        if len(invoices_fks) < 2:  # Should have FKs to suppliers and workspaces
            print("❌ Invoice foreign keys missing")
            return False

        print("✅ Table structure correct")
        print(f"   - Users table: {len(users_columns)} columns")
        print(f"   - Invoice foreign keys: {len(invoices_fks)}")
        return True
    except Exception as e:
        print(f"❌ Structure check failed: {e}")
        return False


def test_models():
    """Test SQLAlchemy models"""
    print("\n🔍 Testing SQLAlchemy models...")
    try:
        from app.core.database import SessionLocal
        from app.models import User, Workspace

        db = SessionLocal()

        # Test query (should return empty list, not error)
        users = db.query(User).all()
        workspaces = db.query(Workspace).all()

        db.close()

        print("✅ Models work correctly")
        print(f"   - Current users: {len(users)}")
        print(f"   - Current workspaces: {len(workspaces)}")
        return True
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        return False


def test_env_config():
    """Test environment configuration"""
    print("\n🔍 Testing environment configuration...")
    try:
        from app.core.config import settings

        if 'your_' in settings.DATABASE_URL.lower():
            print("⚠️  Database URL contains placeholder values")
            print("   Update DATABASE_URL in .env file")
            return False

        if 'your_' in settings.GOOGLE_CLIENT_ID.lower():
            print("⚠️  Google OAuth not configured (expected for Phase 1)")

        if 'your_' in settings.ANTHROPIC_API_KEY.lower():
            print("⚠️  Anthropic API key not configured (expected for Phase 1)")

        print("✅ Environment configuration loaded")
        print(f"   - Environment: {settings.ENVIRONMENT}")
        print(f"   - Database URL: {settings.DATABASE_URL[:30]}...")
        return True
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False


def run_all_tests():
    """Run all tests and report results"""
    print("=" * 60)
    print("PHASE 1 TESTING - Backend Foundation")
    print("=" * 60)

    tests = [
        ("Imports", test_imports),
        ("Environment Config", test_env_config),
        ("Database Connection", test_database_connection),
        ("Tables Exist", test_tables_exist),
        ("Table Structure", test_table_structure),
        ("SQLAlchemy Models", test_models),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"❌ {name} - Unexpected error: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, p in results if p)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")

    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 SUCCESS! Phase 1 is working correctly!")
        print("\nNext steps:")
        print("1. Test the API: curl http://localhost:8000/health")
        print("2. View docs: http://localhost:8000/docs")
        print("3. Ready for Phase 2: Authentication")
    else:
        print("\n⚠️  Some tests failed. See TESTING_PHASE1.md for troubleshooting.")

    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
