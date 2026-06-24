from app import create_app
from app.models import db
from app.models.user import User

app = create_app()

def run():
    with app.app_context():
        email = input("Admin email: ")
        display_name = input("Admin display name: ")
        password = input("Password: ")

        existing = User.query.filter_by(email=email).first()
        if existing:
            print("User exists; updating to admin and setting password")
            existing.set_password(password)
            existing.role = 'admin'
            existing.display_name = display_name or existing.display_name
            db.session.commit()
        else:
            u = User(display_name=display_name, email=email, role='admin')
            u.set_password(password)
            db.session.add(u)
            db.session.commit()

        print("Admin user created/updated.")

if __name__ == '__main__':
    run()
