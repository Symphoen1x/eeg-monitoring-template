
from app.db.database import SessionLocal
from app.db.models import User
import sys

def check_user(email):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            print(f"✅ User found: {user.email} (ID: {user.id})")
        else:
            print(f"❌ User not found: {email}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    email = "afif@gmail.com"
    if len(sys.argv) > 1:
        email = sys.argv[1]
    check_user(email)
