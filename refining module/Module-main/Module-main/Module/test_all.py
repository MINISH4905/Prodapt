"""
VentureX-Ray - Unified Module Test Suite (test_all.py)
-------------------------------------------------------
End-to-end integration and smoke test runner for all platform modules:
1. `test_attacker_module()`: Validates Attacker Module stub server (Modules 1-3).
2. `test_defense_module()`: Validates Defense & Refinement Engine (Modules 4-6) FastAPI endpoints and templates catalog.
3. `test_investor_module()`: Validates Investor Simulation stub server (Modules 7-11).
"""

import sys
import os

# Add workspace directory to sys.path so modules can be imported directly
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

def test_attacker_module():
    """Validates root endpoint of Attacker Module (Modules 1-3 stub)."""
    print("Testing Attacker Module...")
    try:
        from fastapi.testclient import TestClient
        from attacker_module.backend.main import app as attacker_app
        
        client = TestClient(attacker_app)
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        assert "Attacker Module (Stub)" in response.text
        print("[OK] Attacker module root serves frontend HTML stub.")
    except Exception as e:
        print(f"[FAIL] Attacker module test failed: {e}")
        raise e

def test_defense_module():
    """Validates FastAPI endpoints and startup catalog of Defense Engine (Modules 4-6)."""
    print("Testing Defense Module...")
    try:
        from fastapi.testclient import TestClient
        from defense_module.backend.main import app as defense_app
        
        client = TestClient(defense_app)
        
        # Test index page serving
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        assert "Defense & Refinement Engine" in response.text
        print("[OK] Defense module root serves frontend dashboard HTML.")
        
        # Test GET /api/startups endpoint
        response = client.get("/api/startups")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert any(item["key"] == "ecopacker" for item in data)
        print("[OK] GET /api/startups returned all startup templates.")
    except Exception as e:
        print(f"[FAIL] Defense module test failed: {e}")
        raise e

def test_investor_module():
    """Validates root endpoint of Investor Module (Modules 7-11 stub)."""
    print("Testing Investor Module...")
    try:
        from fastapi.testclient import TestClient
        from investor_module.backend.main import app as investor_app
        
        client = TestClient(investor_app)
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        assert "Investor Module (Stub)" in response.text
        print("[OK] Investor module root serves frontend HTML stub.")
    except Exception as e:
        print(f"[FAIL] Investor module test failed: {e}")
        raise e

if __name__ == "__main__":
    print("Running VentureX-Ray Unified Modules Test Suite...\n")
    test_attacker_module()
    print()
    test_defense_module()
    print()
    test_investor_module()
    print("\nAll modules verified successfully!")

