from flask_pymongo import PyMongo

mongo = PyMongo()

def init_app(app):
    mongo.__init__(app)
    return mongo