def register_blueprints(app):
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp
    from app.routes.auth import auth_bp
    from app.routes.backup import backup_bp
    from app.routes.categories import categories_bp
    from app.routes.contacts import contacts_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.labs import labs_bp
    from app.routes.notes import notes_bp
    from app.routes.notifications import notifications_bp
    from app.routes.profile import profile_bp
    from app.routes.scheduled_tasks import tasks_bp
    from app.routes.security import security_bp
    from app.routes.topics import topics_bp

    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(backup_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(topics_bp)
    app.register_blueprint(contacts_bp)
    app.register_blueprint(labs_bp)
    app.register_blueprint(notes_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(security_bp)
    app.register_blueprint(tasks_bp)
