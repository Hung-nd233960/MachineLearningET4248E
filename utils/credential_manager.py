# pylint: disable=missing-module-docstring

import os
import hashlib
from uuid import UUID, uuid4
from typing import Dict, List, Optional
import toml
from pydantic import BaseModel, Field
from pydantic import ValidationError


class User(BaseModel):
    uuid: UUID = Field(default_factory=uuid4)
    password: str
    role: str = "Labeler"


class CredentialManager:
    def __init__(self, toml_file: str = "users.toml") -> None:
        self.toml_file = toml_file
        self.users: Dict[str, User] = self._load_users()

    def _load_users(self) -> Dict[str, User]:
        if not os.path.exists(self.toml_file):
            return {}

        raw_data = toml.load(self.toml_file).get("users", {})
        users: Dict[str, User] = {}

        for username, user_data in raw_data.items():
            try:
                users[username] = User(**user_data)
            except (ValidationError, TypeError) as e:
                print(f"⚠️ Skipping invalid user '{username}': {e}")

        return users

    def _save_users(self) -> None:
        data_to_save = {
            "users": {
                name: {
                    "uuid": str(user.uuid),
                    "password": user.password,
                    "role": user.role,
                }
                for name, user in self.users.items()
            }
        }
        with open(self.toml_file, "w", encoding="utf-8") as f:
            toml.dump(data_to_save, f)

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def add_user(self, username: str, password: str, role: str) -> bool:
        """Add a new user with a hashed password."""
        if username in self.users:
            print(f"User '{username}' already exists.")
            return False

        hashed_pw = self._hash_password(password)
        self.users[username] = User(password=hashed_pw, role=role.lower())
        self._save_users()
        print(f"User '{username}' added with uuid {self.users[username].uuid}.")
        return True

    def verify_user(self, username: str, password: str) -> bool:
        """Verify if the provided username and password match."""
        user: Optional[User] = self.users.get(username)
        if not user:
            return False
        return self._hash_password(password) == user.password

    def list_users(self) -> List[str]:
        """List all usernames in the credential manager by keys."""
        return list(self.users.keys())

    def reset(self) -> None:
        """Reloads user data from the TOML file, discarding current state."""
        self.users = self._load_users()

    def get_user_id(self, username: str) -> Optional[UUID]:
        """Get the UUID of a user by username."""
        user = self.users.get(username)
        if user:
            return user.uuid
        return None

    def get_user_role(self, username: str) -> Optional[str]:
        """Get the role of a user by username."""
        user = self.users.get(username)
        if user:
            return user.role
        return None

    def get_username_by_id(self, user_id: str) -> Optional[str]:
        user_id = UUID(user_id) if isinstance(user_id, str) else user_id
        """Get the username by user uuid."""
        for username, user in self.users.items():
            if user.uuid == user_id:
                return username
        return None


if __name__ == "__main__":
    cm = CredentialManager()
    print("Current users:", cm.list_users())
    print(cm.get_user_id("verifier1"))
    print(cm.get_user_role("verifier1"))
    print(cm.get_username_by_id((cm.get_user_id("verifier1"))))
