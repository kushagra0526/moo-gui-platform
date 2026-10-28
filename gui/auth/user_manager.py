"""
Production-grade user management system
"""

import hashlib
import hmac
import os
import secrets
import threading
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any

# User database path
USER_DB_PATH = Path(__file__).parent.parent.parent / "database" / "users.json"
USER_DB_PATH.parent.mkdir(exist_ok=True)
PBKDF2_ITERATIONS = 200_000
_db_lock = threading.Lock()  # serialises read-modify-write of users.json within this process

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
        """Save user database atomically, so a crash or concurrent read never sees a half-written file."""
        tmp = self.db_path.with_suffix(".tmp")
        with open(tmp, 'w') as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, self.db_path)
    
    def _hash_password(self, password: str, salt: str = None) -> Tuple[str, str]:
        """
        Hash password with salt using PBKDF2-HMAC-SHA256.
        Returns (hash, salt)
        """
        if salt is None:
            salt = secrets.token_hex(32)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), PBKDF2_ITERATIONS)
        return pwd_hash.hex(), salt
    
    def _verify_password(self, user: Dict[str, Any], password: str) -> bool:
        """Verify password against the stored hash; accounts created before PBKDF2 use one SHA-256 round."""
        if user.get("kdf") == "pbkdf2":
            pwd_hash, _ = self._hash_password(password, user["salt"])
        else:
            pwd_hash = hashlib.sha256(f"{password}{user['salt']}".encode('utf-8')).hexdigest()
        return hmac.compare_digest(pwd_hash, user["password_hash"])
    
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
        
        # Hash outside the lock: it is deliberately slow
        pwd_hash, salt = self._hash_password(password)

        with _db_lock:
            return self._add_user(email, full_name, pwd_hash, salt)

    def _add_user(self, email: str, full_name: str, pwd_hash: str, salt: str) -> Tuple[bool, str]:
        db = self._load_db()
        if email in db:
            return False, "An account with this email already exists"

        db[email] = {
            "full_name": full_name.strip(),
            "email": email,
            "password_hash": pwd_hash,
            "salt": salt,
            "kdf": "pbkdf2",
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
        with _db_lock:
            return self._authenticate(email, password)

    def _authenticate(self, email: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
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
        if not self._verify_password(user, password):
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
        
        # Successful login - upgrade a legacy hash, reset attempts and update last login
        if user.get("kdf") != "pbkdf2":
            user["password_hash"], user["salt"] = self._hash_password(password)
            user["kdf"] = "pbkdf2"
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
