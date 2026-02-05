import sys
import os

# Ensure app is in path
sys.path.insert(0, os.getcwd())

print("Verifying imports...")

try:
    from app.core.settings import settings
    print(f"Settings loaded: DB_URL={settings.DATABASE_URL.split('://')[0]}://...")
except ImportError as e:
    print(f"Failed to import settings: {e}")
    sys.exit(1)

try:
    from app.modules.assessment import models as assessment_models
    print("Assessment models imported.")
    q = assessment_models.Question(q_id="TEST001", question_text="Test")
    print(f"Question model instantiated: {q.q_id}")
except ImportError as e:
    print(f"Failed to import assessment models: {e}")
    sys.exit(1)

try:
    from app.core.engines import V6_1ScoringEngine
    print("Scoring Engine imported.")
except ImportError as e:
    print(f"Failed to import engines: {e}")
    sys.exit(1)

try:
    from app.core.repositories import QuestionRepository
    print("Repositories imported.")
except ImportError as e:
    print(f"Failed to import repositories: {e}")
    sys.exit(1)

try:
    # Check ingest_excel imports (by importing the module)
    import ingest_excel
    print("ingest_excel module imported.")
except ImportError as e:
    print(f"Failed to import ingest_excel: {e}")
    sys.exit(1)

try:
    # Check alembic env imports (simulate partial load)
    from app.models import Base
    print(f"Base imported. Metadata tables: {list(Base.metadata.tables.keys())}")
except ImportError as e:
    print(f"Failed to import Base: {e}")
    sys.exit(1)

print("ALL CHECKS PASSED.")
