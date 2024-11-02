# utils/auth.py
import os
from dotenv import load_dotenv
import jwt
import bcrypt
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class AuthHandler:
    def __init__(self):
        load_dotenv()
        self.secret_key = os.getenv('JWT_SECRET_KEY')
        if not self.secret_key:
            raise ValueError("JWT_SECRET_KEY not found in environment variables")

        # Initialize with default admin user
        admin_email = 'zack@fairnessfactor.com'
        admin_password = "1122Kryptic$"
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(admin_password.encode('utf-8'), salt)

        self.users = {
            admin_email: {
                'password': hashed_password,
                'name': 'Admin User',
                'role': 'admin',
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'created_by': 'system'
            }
        }

    def verify_email_domain(self, email):
        """Verify email belongs to Fairness Factor domain."""
        email = email.lower()
        return email.endswith('fairnessfactor.com')

    def add_user(self, email, password, name, added_by, role='user'):
        """Add a new user to the system."""
        try:
            if not self.verify_email_domain(email):
                raise ValueError("Only Fairness Factor email addresses are allowed")

            if any(existing.lower() == email.lower() for existing in self.users.keys()):
                raise ValueError("User already exists")

            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)

            self.users[email] = {
                'password': hashed,
                'name': name,
                'role': role,
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'created_by': added_by
            }
            return True

        except Exception as e:
            logger.error(f"Error adding user {email}: {str(e)}")
            raise

    def login(self, email, password):
        """Authenticate user and return JWT token."""
        try:
            matching_email = next(
                (stored_email for stored_email in self.users.keys()
                 if stored_email.lower() == email.lower()),
                None
            )

            if not matching_email:
                return None

            stored_password = self.users[matching_email]['password']
            if isinstance(stored_password, str):
                stored_password = stored_password.encode('utf-8')

            if bcrypt.checkpw(password.encode('utf-8'), stored_password):
                token = jwt.encode({
                    'email': matching_email,
                    'name': self.users[matching_email]['name'],
                    'role': self.users[matching_email].get('role', 'user'),
                    'exp': datetime.utcnow() + timedelta(days=1)
                }, self.secret_key, algorithm='HS256')

                return token

            return None

        except Exception as e:
            logger.error(f"Login error for {email}: {str(e)}")
            return None

    def verify_token(self, token):
        """Verify JWT token and return user info."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            matching_email = next(
                (stored_email for stored_email in self.users.keys()
                 if stored_email.lower() == payload['email'].lower()),
                None
            )

            if matching_email:
                return {
                    'email': matching_email,
                    'name': self.users[matching_email]['name'],
                    'role': self.users[matching_email].get('role', 'user')
                }

            return None

        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            return None