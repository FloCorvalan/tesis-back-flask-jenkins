import pytest
from apps import create_app

@pytest.fixture(scope='session')
def test_client():
    app, mongo = create_app('config.TestConfig')

    # Create a test client using the Flask application configured for testing
    with app.test_client() as testing_client:
        # Establish an application context
        with app.app_context():
            yield testing_client, mongo  # this is where the testing happens!
