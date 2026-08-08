import sys
import os

# Add the workspace root to python path to import correctly
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

def test_imports_and_mock_data():
    """Verify that backend schemas, agents, and mock data can be imported without error."""
    print("Testing backend imports...")
    try:
        from defense_module.backend.schemas import StartupProfile, VulnerabilityMap, ClarityQuestion
        from defense_module.backend.mock_inputs import MOCK_STARTUPS
        from defense_module.backend.agents import clean_and_parse_json
        
        print("[OK] Schemas and agents imported successfully.")
        assert "ecopacker" in MOCK_STARTUPS
        assert "medroute" in MOCK_STARTUPS
        assert "orbitlink" in MOCK_STARTUPS
        print("[OK] Mock startup templates verified.")
    except Exception as e:
        print(f"[FAIL] Import test failed: {str(e)}")
        raise e

def test_api_endpoints():
    """Test FastAPI application endpoints using TestClient."""
    print("Testing API endpoints via FastAPI TestClient...")
    try:
        from fastapi.testclient import TestClient
        from defense_module.backend.main import app
        
        client = TestClient(app)
        
        # Test GET /api/startups
        response = client.get("/api/startups")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["key"] == "ecopacker"
        print("[OK] GET /api/startups returned 200 OK with correct mock templates.")
        
        # Test index response
        response = client.get("/")
        assert response.status_code == 200
        print("[OK] Root index.html serving verified.")
        
    except Exception as e:
        print(f"[FAIL] API endpoint testing failed: {str(e)}")
        raise e

if __name__ == "__main__":
    print("Running VentureX-Ray Defense Module Tests...")
    test_imports_and_mock_data()
    test_api_endpoints()
    print("\nAll unit tests passed successfully!")
