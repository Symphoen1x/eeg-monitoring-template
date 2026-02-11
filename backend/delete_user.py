
from app.db.database import SessionLocal
from app.db.models import User
import sys

def delete_user(email):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            db.delete(user)
            db.commit()
            print(f"✅ User deleted: {email}")
        else:
            print(f"User not found: {email}")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    email = "afif@gmail.com"
    delete_user(email)
