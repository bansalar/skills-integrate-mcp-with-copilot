import getpass
import json
import os
import sys
from pathlib import Path

from teacher_auth import hash_password


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python src/manage_teachers.py <username>")
        return 2

    username = sys.argv[1].strip()
    if not username:
        print("Username cannot be empty")
        return 2

    password = getpass.getpass("Teacher password (12+ characters): ")
    if len(password) < 12:
        print("Password must be at least 12 characters")
        return 2
    if password != getpass.getpass("Confirm password: "):
        print("Passwords do not match")
        return 2

    teachers_file = Path(os.environ.get("TEACHERS_FILE", Path(__file__).with_name("teachers.json")))
    try:
        data = json.loads(teachers_file.read_text(encoding="utf-8")) if teachers_file.exists() else {"teachers": []}
    except (OSError, json.JSONDecodeError) as error:
        print(f"Could not read {teachers_file}: {error}")
        return 1

    teachers = data.setdefault("teachers", [])
    if any(teacher.get("username") == username for teacher in teachers):
        print(f"Teacher {username!r} already exists")
        return 1

    teachers.append({"username": username, **hash_password(password)})
    teachers_file.parent.mkdir(parents=True, exist_ok=True)
    teachers_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    os.chmod(teachers_file, 0o600)
    print(f"Added teacher {username!r} to {teachers_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())