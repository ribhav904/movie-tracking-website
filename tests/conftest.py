import os

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://user:password@localhost:5432/postgres")
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_PUBLISHABLE_KEY", "test-publishable-key")
os.environ.setdefault("SUPABASE_SECRET_KEY", "test-secret-key")
os.environ.setdefault("OPEN_LIBRARY_CONTACT", "tests@example.com")
