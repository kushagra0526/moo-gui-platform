"""
Production-grade user management system
"""

import hashlib
import secrets
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any

# User database path
USER_DB_PATH = Path(__file__).parent.parent.parent / "database" / "users.json"
USER_DB_PATH.parent.mkdir(exist_ok=True)

class PasswordValidator:
    """Validate password strength."""
    
    @staticmethod
    def validate(password: str) -> Tuple[bool, str]:
        """
        Validate password meets security requirements.
        Returns (is_valid, error_message)
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain at least one number"
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character (!@#$%^&*...)"
        
        return True, ""

class EmailValidator:
    """Validate email format."""
    
    @staticmethod
    def validate(email: str) -> Tuple[bool, str]:
        """
        Validate email format.
        Returns (is_valid, error_message)
        """
        if not email:
            return False, "Email is required"
        
        # Basic email regex
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, "Invalid email format"
        
        return True, ""

class UserManager:
    """Manage user accounts with production-grade security."""
    
    def __init__(self):
        self.db_path = USER_DB_PATH
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """Create database file if it doesn't exist."""
        if not self.db_path.exists():
            self._save_db({})
    
    def _load_db(self) -> Dict[str, Any]:
        """Load user database."""
        try:
            with open(self.db_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_db(self, data: Dict[str, Any]):
        """Save user database."""
        with open(self.db_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _hash_password(self, password: str, salt: str = None) -> Tuple[str, str]:
        """
        Hash password with salt using SHA-256.
        Returns (hash, salt)
        """
        if salt is None:
            salt = secrets.token_hex(32)
        
        # Combine password and salt, then hash
        pwd_salt = f"{password}{salt}".encode('utf-8')
        pwd_hash = hashlib.sha256(pwd_salt).hexdigest()
        
        return pwd_hash, salt
    
    def _verify_password(self, password: str, stored_hash: str, salt: str) -> bool:
        """Verify password against stored hash."""
        pwd_hash, _ = self._hash_password(password, salt)
        return pwd_hash == stored_hash
    
    def register_user(self, email: str, full_name: str, password: str) -> Tuple[bool, str]:
        """
        Register a new user.
        Returns (success, message)
        """
        # Validate email
        email = email.lower().strip()
        is_valid, error = EmailValidator.validate(email)
        if not is_valid:
            return False, error
        
        # Validate full name
        if not full_name or len(full_name.strip()) < 2:
            return False, "Full name must be at least 2 characters"
        
        # Validate password
        is_valid, error = PasswordValidator.validate(password)
        if not is_valid:
            return False, error
        
        # Check if user already exists
        db = self._load_db()
        if email in db:
            return False, "An account with this email already exists"
        
        # Hash password with salt
        pwd_hash, salt = self._hash_password(password)
        
        # Create user record
        db[email] = {
            "full_name": full_name.strip(),
            "email": email,
            "password_hash": pwd_hash,
            "salt": salt,
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "login_attempts": 0,
            "account_locked": False,
            "locked_until": None
        }
        
        self._save_db(db)
        return True, "Account created successfully"
    
    def authenticate_user(self, email: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Authenticate user credentials.
        Returns (success, message, user_data)
        """
        email = email.lower().strip()
        db = self._load_db()
        
        # Check if user exists
        if email not in db:
            return False, "Invalid email or password", None
        
        user = db[email]
        
        # Check if account is locked
        if user.get("account_locked", False):
            locked_until = user.get("locked_until")
            if locked_until:
                unlock_time = datetime.fromisoformat(locked_until)
                if datetime.now() < unlock_time:
                    remaining = (unlock_time - datetime.now()).seconds // 60
                    return False, f"Account locked. Try again in {remaining} minutes", None
                else:
                    # Unlock account
                    user["account_locked"] = False
                    user["locked_until"] = None
                    user["login_attempts"] = 0
        
        # Verify password
        if not self._verify_password(password, user["password_hash"], user["salt"]):
            # Increment failed login attempts
            user["login_attempts"] = user.get("login_attempts", 0) + 1
            
            # Lock account after 5 failed attempts
            if user["login_attempts"] >= 5:
                user["account_locked"] = True
                user["locked_until"] = (datetime.now() + timedelta(minutes=15)).isoformat()
                self._save_db(db)
                return False, "Too many failed attempts. Account locked for 15 minutes", None
            
            self._save_db(db)
            remaining_attempts = 5 - user["login_attempts"]
            return False, f"Invalid email or password. {remaining_attempts} attempts remaining", None
        
        # Successful login - reset attempts and update last login
        user["login_attempts"] = 0
        user["last_login"] = datetime.now().isoformat()
        user["account_locked"] = False
        user["locked_until"] = None
        self._save_db(db)
        
        # Return user data (without sensitive info)
        user_data = {
            "email": user["email"],
            "full_name": user["full_name"],
            "created_at": user["created_at"],
            "last_login": user["last_login"]
        }
        
        return True, "Login successful", user_data
    
    def change_password(self, email: str, old_password: str, new_password: str) -> Tuple[bool, str]:
        """
        Change user password.
        Returns (success, message)
        """
        email = email.lower().strip()
        db = self._load_db()
        
        if email not in db:
            return False, "User not found"
        
        user = db[email]
        
        # Verify old password
        if not self._verify_password(old_password, user["password_hash"], user["salt"]):
            return False, "Current password is incorrect"
        
        # Validate new password
        is_valid, error = PasswordValidator.validate(new_password)
        if not is_valid:
            return False, error
        
        # Hash new password
        pwd_hash, salt = self._hash_password(new_password)
        user["password_hash"] = pwd_hash
        user["salt"] = salt
        
        self._save_db(db)
        return True, "Password changed successfully"
    
    def get_user_info(self, email: str) -> Optional[Dict]:
        """Get user information (without sensitive data)."""
        email = email.lower().strip()
        db = self._load_db()
        
        if email not in db:
            return None
        
        user = db[email]
        return {
            "email": user["email"],
            "full_name": user["full_name"],
            "created_at": user["created_at"],
            "last_login": user.get("last_login")
        }
