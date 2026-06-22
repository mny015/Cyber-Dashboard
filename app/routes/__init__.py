def register_blueprints(app):
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)