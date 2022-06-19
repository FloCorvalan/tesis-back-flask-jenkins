import os

class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class ProductionConfig(Config):
    DEBUG = False
    MONGO_URI = os.environ.get('DATABASE_URL')

class DevelopmentConfig(Config):
    ENV="development"
    DEVELOPMENT=True
    DEBUG=True
    MONGO_URI=os.environ.get('DATABASE_DEV_URL')

class TestConfig(Config):
    ENV="test"
    TESTING=True
    DEVELOPMENT=False
    DEBUG=False
    MONGO_URI=os.environ.get('DATABASE_TEST_URL')