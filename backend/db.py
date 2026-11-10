import os
import json
import uuid
import time
from datetime import datetime, timezone
from pymongo import MongoClient, DESCENDING
from pymongo.errors import PyMongoError

class DatabaseManager:
    def __init__(self):
        self.mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
        self.db_name = os.getenv("MONGO_DB", "genai_content_transformation")
        self.client = None
        self.db = None
        self.is_connected = False
        self.last_ping_attempt = 0
        self.fallback_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "local_storage.json")
        self._init_connection()

    def _init_connection(self):
        self.last_ping_attempt = time.time()
        try:
            self.client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=500)
            self.client.admin.command("ping")
            self.db = self.client[self.db_name]
            self.db["users"].create_index("email", unique=True)
            self.db["transformations"].create_index([("user_id", 1), ("created_at", DESCENDING)])
            self.is_connected = True
        except Exception:
            self.is_connected = False
            self.client = None
            self.db = None
            self._ensure_fallback_file()

    def _ensure_fallback_file(self):
        os.makedirs(os.path.dirname(self.fallback_file), exist_ok=True)
        if not os.path.exists(self.fallback_file):
            with open(self.fallback_file, "w", encoding="utf-8") as f:
                json.dump({"users": [], "transformations": []}, f, indent=2)

    def _read_fallback(self):
        self._ensure_fallback_file()
        try:
            with open(self.fallback_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"users": [], "transformations": []}

    def _write_fallback(self, data):
        self._ensure_fallback_file()
        try:
            with open(self.fallback_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception:
            return False

    def ping(self):
        if self.is_connected:
            return True
        if time.time() - self.last_ping_attempt > 30:
            self._init_connection()
        return self.is_connected

    # User operations
    def create_user(self, name, email, password_hash):
        email_clean = email.strip().lower()
        if self.ping():
            try:
                res = self.db["users"].insert_one({
                    "name": name.strip(),
                    "email": email_clean,
                    "password_hash": password_hash,
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
                return str(res.inserted_id)
            except Exception as e:
                if "duplicate" in str(e).lower():
                    raise ValueError("An account with this email already exists.")
                raise e
        else:
            # Fallback
            data = self._read_fallback()
            for u in data.get("users", []):
                if u.get("email") == email_clean:
                    raise ValueError("An account with this email already exists.")
            new_id = str(uuid.uuid4())
            data.setdefault("users", []).append({
                "id": new_id,
                "name": name.strip(),
                "email": email_clean,
                "password_hash": password_hash,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            self._write_fallback(data)
            return new_id

    def get_user_by_email(self, email):
        email_clean = email.strip().lower()
        if self.ping():
            try:
                from bson import ObjectId
                user = self.db["users"].find_one({"email": email_clean})
                if user:
                    user["id"] = str(user.pop("_id"))
                return user
            except Exception:
                pass
        # Fallback
        data = self._read_fallback()
        for u in data.get("users", []):
            if u.get("email") == email_clean:
                return u
        return None

    def get_user_by_id(self, user_id):
        if not user_id:
            return None
        if self.ping():
            try:
                from bson import ObjectId
                user = self.db["users"].find_one({"_id": ObjectId(user_id)})
                if user:
                    user["id"] = str(user.pop("_id"))
                    return user
            except Exception:
                pass
        # Fallback
        data = self._read_fallback()
        for u in data.get("users", []):
            if u.get("id") == str(user_id):
                return u
        return None

    # Transformations
    def save_transformation(self, user_id, source, output, format_type, audience="General", tone="Professional", detail="Medium", title=""):
        if not title:
            title = f"{format_type} - {datetime.now().strftime('%b %d, %H:%M')}"
        record = {
            "user_id": str(user_id) if user_id else "guest",
            "title": title,
            "source": source[:25000],
            "output": output,
            "format": format_type,
            "audience": audience,
            "tone": tone,
            "detail": detail,
            "words_input": len(source.split()),
            "words_output": len(output.split()),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        if self.ping():
            try:
                res = self.db["transformations"].insert_one(record)
                record["id"] = str(res.inserted_id)
                return record
            except Exception:
                pass
        # Fallback
        data = self._read_fallback()
        record["id"] = str(uuid.uuid4())
        data.setdefault("transformations", []).insert(0, record)
        self._write_fallback(data)
        return record

    def get_user_history(self, user_id=None, limit=50):
        items = []
        uid_str = str(user_id) if user_id else "guest"
        if self.ping():
            try:
                from bson import ObjectId
                query = {"user_id": uid_str} if user_id else {}
                cursor = self.db["transformations"].find(query).sort("_id", DESCENDING).limit(limit)
                for item in cursor:
                    item["id"] = str(item.pop("_id"))
                    items.append(item)
                return items
            except Exception:
                pass
        # Fallback
        data = self._read_fallback()
        all_items = data.get("transformations", [])
        if user_id:
            items = [t for t in all_items if t.get("user_id") == uid_str][:limit]
        else:
            items = all_items[:limit]
        return items

    def get_transformation_by_id(self, item_id, user_id=None):
        if not item_id:
            return None
        if self.ping():
            try:
                from bson import ObjectId
                q = {"_id": ObjectId(item_id)}
                if user_id:
                    q["user_id"] = str(user_id)
                item = self.db["transformations"].find_one(q)
                if item:
                    item["id"] = str(item.pop("_id"))
                    return item
            except Exception:
                pass
        # Fallback
        data = self._read_fallback()
        for t in data.get("transformations", []):
            if t.get("id") == str(item_id):
                if not user_id or t.get("user_id") == str(user_id):
                    return t
        return None

    def delete_transformation(self, item_id, user_id=None):
        if not item_id:
            return False
        if self.ping():
            try:
                from bson import ObjectId
                q = {"_id": ObjectId(item_id)}
                if user_id:
                    q["user_id"] = str(user_id)
                res = self.db["transformations"].delete_one(q)
                return res.deleted_count > 0
            except Exception:
                pass
        # Fallback
        data = self._read_fallback()
        before = len(data.get("transformations", []))
        data["transformations"] = [
            t for t in data.get("transformations", [])
            if not (t.get("id") == str(item_id) and (not user_id or t.get("user_id") == str(user_id)))
        ]
        if len(data["transformations"]) < before:
            self._write_fallback(data)
            return True
        return False

    def clear_user_history(self, user_id):
        if not user_id:
            return False
        uid_str = str(user_id)
        if self.ping():
            try:
                self.db["transformations"].delete_many({"user_id": uid_str})
                return True
            except Exception:
                pass
        data = self._read_fallback()
        data["transformations"] = [t for t in data.get("transformations", []) if t.get("user_id") != uid_str]
        self._write_fallback(data)
        return True

    def get_dashboard_stats(self, user_id):
        history = self.get_user_history(user_id=user_id, limit=200)
        total_transformations = len(history)
        words_in = sum(item.get("words_input", 0) for item in history)
        words_out = sum(item.get("words_output", 0) for item in history)
        
        format_counts = {}
        for item in history:
            fmt = item.get("format", "Other")
            format_counts[fmt] = format_counts.get(fmt, 0) + 1
        
        return {
            "total_transformations": total_transformations,
            "words_input": words_in,
            "words_output": words_out,
            "format_breakdown": format_counts,
            "recent_items": history[:5],
            "mongodb_connected": self.is_connected,
            "storage_mode": "MongoDB" if self.is_connected else "Local File Storage"
        }

db = DatabaseManager()
