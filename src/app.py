from apps import create_app

if __name__ == "__main__":
    app, mongo = create_app('config.DevelopmentConfig')
    app.run(port=5000)