import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home_page(client):
    """Test that the homepage loads (Status 200)."""
    rv = client.get('/')
    assert rv.status_code == 200

def test_student_name_exists(client):
    """Test if the Student Name from ConfigMap is being passed to the template."""
    rv = client.get('/')
    # Replace 'Winlyn' with whatever name you expect to see
    assert b"Winlyn" in rv.data 

def test_about_page(client):
    """Test that the /about route is reachable."""
    rv = client.get('/about')
    assert rv.status_code == 200