"""
Test suite for ARTIFACTOR v3.0 Backend
Comprehensive testing including v2.0 compatibility
"""

import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool
import os
import tempfile
from pathlib import Path

from backend.main import app
from backend.database import get_database, Base
from backend.config import settings
from backend.models import User, Artifact

# Test database URL (in-memory SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
    echo=False
)

@pytest.fixture
async def db_session():
    """Create test database session"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(test_engine) as session:
        yield session

@pytest.fixture
async def client(db_session):
    """Create test client with database override"""

    async def override_get_database():
        yield db_session

    app.dependency_overrides[get_database] = override_get_database

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()

@pytest.fixture
async def test_user(db_session):
    """Create test user"""
    from backend.routers.auth import AuthService
    auth_service = AuthService()

    user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        hashed_password=auth_service.hash_password("testpassword"),
        is_active=True
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture
async def test_artifact(db_session, test_user):
    """Create test artifact"""
    artifact = Artifact(
        title="Test Artifact",
        description="Test Description",
        content="print('Hello, World!')",
        file_type="python",
        file_extension=".py",
        language="python",
        file_size=22,
        checksum="test_checksum",
        owner_id=test_user.id
    )

    db_session.add(artifact)
    await db_session.commit()
    await db_session.refresh(artifact)
    return artifact

class TestHealth:
    """Test health and system endpoints"""

    async def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "ARTIFACTOR v3.0"
        assert data["version"] == "3.0.0"

    async def test_health_check(self, client):
        """Test health check endpoint"""
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "database" in data
        assert "version" in data

class TestAuthentication:
    """Test authentication endpoints"""

    async def test_register_user(self, client):
        """Test user registration"""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepassword",
            "full_name": "New User"
        }

        response = await client.post("/api/auth/register", json=user_data)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"

    async def test_login_user(self, client, test_user):
        """Test user login"""
        login_data = {
            "username": "testuser",
            "password": "testpassword"
        }

        response = await client.post("/api/auth/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        login_data = {
            "username": "nonexistent",
            "password": "wrongpassword"
        }

        response = await client.post("/api/auth/login", json=login_data)
        assert response.status_code == 401

    async def test_get_current_user(self, client, test_user):
        """Test getting current user info"""
        # First login
        login_data = {
            "username": "testuser",
            "password": "testpassword"
        }

        login_response = await client.post("/api/auth/login", json=login_data)
        token = login_response.json()["access_token"]

        # Get user info
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get("/api/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"

class TestAgentBridge:
    """Test agent coordination bridge"""

    async def test_agent_bridge_status(self, client):
        """Test agent bridge status"""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "agent_bridge_status" in data

    @pytest.mark.asyncio
    async def test_agent_invocation(self, client):
        """Test agent invocation through bridge"""
        # This would test the agent bridge functionality
        # For now, just test that the bridge is available
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "agent_bridge" in data

class TestV2Compatibility:
    """Test v2.0 compatibility features"""

    @pytest.fixture
    def temp_v2_files(self):
        """Create temporary v2.0-style files for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create sample artifact files
            (temp_path / "test_script.py").write_text("print('Hello from v2.0')")
            (temp_path / "config.json").write_text('{"setting": "value"}')
            (temp_path / "README.md").write_text("# Test Project")

            yield temp_path

    async def test_v2_detection(self, temp_v2_files):
        """Test v2.0 installation detection"""
        from backend.services.agent_bridge import AgentCoordinationBridge

        bridge = AgentCoordinationBridge()
        bridge.v2_path = temp_v2_files
        await bridge.initialize()

        status = bridge.get_status()
        assert status["v2_path"] is not None

    async def test_migration_import(self, db_session, temp_v2_files):
        """Test v2.0 to v3.0 migration"""
        from backend.migration.v2_importer import V2DataImporter

        importer = V2DataImporter(str(temp_v2_files))
        artifacts_migrated = await importer.migrate_artifacts(db_session)

        assert artifacts_migrated > 0

        # Check migration summary
        summary = importer.get_migration_summary()
        assert summary["imported_artifacts"] > 0
        assert summary["success_rate"] > 0

class TestPerformance:
    """Test performance and optimization preservation"""

    async def test_coordination_overhead(self):
        """Test that coordination overhead is preserved from v2.0"""
        from backend.services.agent_bridge import AgentCoordinationBridge

        bridge = AgentCoordinationBridge()
        await bridge.initialize()

        # Test agent invocation timing
        import time
        start_time = time.time()

        result = await bridge.invoke_agent("DEBUGGER", {"task_type": "health_check"})

        end_time = time.time()
        execution_time = (end_time - start_time) * 1000  # milliseconds

        # Should maintain v2.0 performance characteristics
        assert execution_time < 100  # Should be well under 100ms
        assert result["success"] is True

    async def test_agent_response_time(self):
        """Test agent response times"""
        from backend.services.agent_bridge import AgentCoordinationBridge

        bridge = AgentCoordinationBridge()
        await bridge.initialize()

        agents_to_test = ["PYGUI", "PYTHON_INTERNAL", "DEBUGGER"]

        for agent_name in agents_to_test:
            start_time = asyncio.get_event_loop().time()
            result = await bridge.invoke_agent(agent_name, {"task_type": "health_check"})
            end_time = asyncio.get_event_loop().time()

            response_time = (end_time - start_time) * 1000  # milliseconds

            assert response_time < 50  # Should respond within 50ms
            assert result.get("success") is True

class TestIntegration:
    """Integration tests for complete workflows"""

    async def test_complete_user_workflow(self, client):
        """Test complete user registration and authentication workflow"""
        # Register user
        user_data = {
            "username": "integrationuser",
            "email": "integration@example.com",
            "password": "integrationpass",
            "full_name": "Integration User"
        }

        register_response = await client.post("/api/auth/register", json=user_data)
        assert register_response.status_code == 200

        # Login
        login_data = {
            "username": "integrationuser",
            "password": "integrationpass"
        }

        login_response = await client.post("/api/auth/login", json=login_data)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Access protected endpoint
        headers = {"Authorization": f"Bearer {token}"}
        me_response = await client.get("/api/auth/me", headers=headers)
        assert me_response.status_code == 200
        assert me_response.json()["username"] == "integrationuser"

# Pytest configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])