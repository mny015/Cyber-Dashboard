def register_blueprints(app):
    from app.routes.api import api_bp
    from app.routes.auth import auth_bp
    from app.routes.categories import categories_bp
    from app.routes.contacts import contacts_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.topics import topics_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(topics_bp)
    app.register_blueprint(contacts_bp)
