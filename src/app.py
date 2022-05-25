from flask import Flask
from database import database

from apps.jenkins.views import jenkins
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)
    # setup with the configuration provided
    app.config.from_object('config.DevelopmentConfig')
    
    # setup all our dependencies
    database.init_app(app)
    
    # register blueprint
    app.register_blueprint(jenkins)
    
    return app

if __name__ == "__main__":
    create_app().run(port=5000)