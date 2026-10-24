import pytest
import mongomock

from app import create_app
from app.config import Config


@pytest.fixture
def client(tmp_path):
    class TestConfig(Config):
        MONGO_CLIENT = mongomock.MongoClient()
        MONGO_DBNAME = "hirehub_test"
        UPLOAD_FOLDER = str(tmp_path / "resumes")
        TESTING = True

    TestConfig.MONGO_CLIENT.drop_database(TestConfig.MONGO_DBNAME)
    app = create_app(TestConfig)
    with app.test_client() as client:
        yield client
