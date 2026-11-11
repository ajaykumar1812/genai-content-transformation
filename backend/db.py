import os
import json
import uuid
import time
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pymongo import MongoClient, DESCENDING
from pymongo.errors import PyMongoError
from config import Config

logger = logging.getLogger("DatabaseManager")

class DatabaseManager:
    """
    MongoDB Atlas database manager with seamless local JSON fallback
    for offline development when no MongoDB cluster is reachable.
    """

    def __init__(self):
        self.mongo_uri = Config.MONGO_URI
        self.db_name = Config.MONGO_DB
        self.client = None
        self.db = None
        self.is_connected = False
        self.last_ping_attempt = 0
        self.fallback_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "local_storage.json"
        )
        self._init_connection()

    def _init_connection(self):
        self.last_ping_attempt = time.time()
        try:
            is_atlas = "mongodb+srv://" in self.mongo_uri or "mongodb.net" in self.mongo_uri
            timeout = Config.MONGO_TIMEOUT_MS if is_atlas else 1500
            client_kwargs = {"serverSelectionTimeoutMS": timeout}

            if is_atlas:
                try:
                    import certifi
                    client_kwargs["tlsCAFile"] = certifi.where()
                except ImportError:
                    pass

            self.client = MongoClient(self.mongo_uri, **client_kwargs)
            # Test connection with a fast admin ping
            self.client.admin.command("ping")
            self.db = self.client[self.db_name]

            # Create required collection indexes
            self.db["users"].create_index("email", unique=True)
            self.db["transformations"].create_index([("user_id", 1), ("created_at", DESCENDING)])
            self.db["user_settings"].create_index("user_id", unique=True)

            self.is_connected = True
            logger.info("Successfully connected to MongoDB (%s)", "Atlas" if is_atlas else "Local")
        except Exception as err:
            self.is_connected = False
            self.client = None
            self.db = None
            self._ensure_fallback_file()
            logger.warning("MongoDB not reachable (%s). Using local storage fallback.", str(err))

    def _ensure_fallback_file(self):
        os.makedirs(os.path.dirname(self.fallback_file), exist_ok=True)
        if not os.path.exists(self.fallback_file):
            with open(self.fallback_file, "w", encoding="utf-8") as f:
                json.dump({"users": [], "transformations": [], "user_settings": []}, f, indent=2)

    def _read_fallback(self) -> Dict[str, Any]:
        self._ensure_fallback_file()
        try:
            with open(self.fallback_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                data.setdefault("users", [])
                data.setdefault("transformations", [])
                data.setdefault("user_settings", [])
                return data
        except Exception:
            return {"users": [], "transformations": [], "user_settings": []}

    def _write_fallback(self, data: Dict[str, Any]) -> bool:
        self._ensure_fallback_file()
        try:
            with open(self.fallback_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error("Failed to write to local storage fallback: %s", str(e))
            return False

    def ping(self) -> bool:
        if self.is_connected and self.client:
            return True
        # Try reconnecting every 30 seconds
        if time.time() - self.last_ping_attempt > 30:
            self._init_connection()
        return self.is_connected

    # ==========================================
    # USER OPERATIONS
    # ==========================================

    def create_user(self, name: str, email: str, password_hash: str) -> str:
        clean_email = email.strip().lower()
        now_iso = datetime.now(timezone.utc).isoformat()

        if self.ping():
            try:
                res = self.db["users"].insert_one({
                    "name": name.strip(),
                    "email": clean_email,
                    "password_hash": password_hash,
                    "created_at": now_iso
                })
                user_id = str(res.inserted_id)
                # Seed default user settings
                self.save_user_settings(user_id, "gemini", Config.GEMINI_MODEL, "dark")
                return user_id
            except Exception as e:
                if "duplicate" in str(e).lower() or "e11000" in str(e).lower():
                    raise ValueError("An account with this email address already exists.")
                raise e
        else:
            data = self._read_fallback()
            for u in data.get("users", []):
                if u.get("email") == clean_email:
                    raise ValueError("An account with this email address already exists.")
            new_id = str(uuid.uuid4())
            new_user = {
                "id": new_id,
                "_id": new_id,
                "name": name.strip(),
                "email": clean_email,
                "password_hash": password_hash,
                "created_at": now_iso
            }
            data["users"].append(new_user)
            self._write_fallback(data)
            self.save_user_settings(new_id, "gemini", Config.GEMINI_MODEL, "dark")
            return new_id

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        clean_email = email.strip().lower()
        if self.ping():
            try:
                u = self.db["users"].find_one({"email": clean_email})
                if u:
                    u["id"] = str(u["_id"])
                return u
            except Exception as e:
                logger.error("Error retrieving user by email from Mongo: %s", str(e))
                return None
        else:
            data = self._read_fallback()
            for u in data.get("users", []):
                if u.get("email") == clean_email:
                    u["id"] = str(u.get("_id") or u.get("id"))
                    return u
            return None

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        if not user_id:
            return None
        if self.ping():
            try:
                from bson.objectid import ObjectId
                query = {"_id": ObjectId(user_id)} if len(user_id) == 24 and all(c in "0123456789abcdef" for c in user_id.lower()) else {"_id": user_id}
                u = self.db["users"].find_one(query)
                if not u:
                    u = self.db["users"].find_one({"id": user_id})
                if u:
                    u["id"] = str(u["_id"])
                return u
            except Exception:
                u = self.db["users"].find_one({"id": user_id})
                if u:
                    u["id"] = str(u["_id"])
                return u
        else:
            data = self._read_fallback()
            for u in data.get("users", []):
                if str(u.get("id")) == str(user_id) or str(u.get("_id")) == str(user_id):
                    u["id"] = str(u.get("_id") or u.get("id"))
                    return u
            return None

    # ==========================================
    # USER SETTINGS OPERATIONS
    # ==========================================

    def get_user_settings(self, user_id: str) -> Dict[str, Any]:
        default_settings = {
            "user_id": user_id,
            "preferred_provider": "gemini",
            "preferred_model": Config.GEMINI_MODEL,
            "theme": "dark",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        if not user_id:
            return default_settings

        if self.ping():
            try:
                s = self.db["user_settings"].find_one({"user_id": str(user_id)})
                if s:
                    s["id"] = str(s["_id"])
                    return s
                return default_settings
            except Exception:
                return default_settings
        else:
            data = self._read_fallback()
            for s in data.get("user_settings", []):
                if str(s.get("user_id")) == str(user_id):
                    return s
            return default_settings

    def save_user_settings(
        self,
        user_id: str,
        preferred_provider: str = "gemini",
        preferred_model: str = "gemini-2.5-flash",
        theme: str = "dark"
    ) -> bool:
        if not user_id:
            return False
        now_iso = datetime.now(timezone.utc).isoformat()
        doc = {
            "user_id": str(user_id),
            "preferred_provider": preferred_provider,
            "preferred_model": preferred_model,
            "theme": theme,
            "updated_at": now_iso
        }
        if self.ping():
            try:
                self.db["user_settings"].update_one(
                    {"user_id": str(user_id)},
                    {"$set": doc},
                    upsert=True
                )
                return True
            except Exception as e:
                logger.error("Failed to save user settings to Mongo: %s", str(e))
                return False
        else:
            data = self._read_fallback()
            settings_list = data.get("user_settings", [])
            updated = False
            for s in settings_list:
                if str(s.get("user_id")) == str(user_id):
                    s.update(doc)
                    updated = True
                    break
            if not updated:
                doc["id"] = str(uuid.uuid4())
                settings_list.append(doc)
            data["user_settings"] = settings_list
            return self._write_fallback(data)

    # ==========================================
    # TRANSFORMATION HISTORY OPERATIONS
    # ==========================================

    def save_transformation(
        self,
        user_id: Optional[str],
        source: str,
        output: str,
        format_type: str,
        audience: str = "General",
        tone: str = "Professional",
        detail: str = "Medium",
        title: Optional[str] = None,
        provider: str = "Google Gemini",
        model: str = "gemini-2.5-flash"
    ) -> Dict[str, Any]:
        """Saves a transformation record associated with the authenticated user."""
        now_iso = datetime.now(timezone.utc).isoformat()
        new_id = str(uuid.uuid4())
        record = {
            "id": new_id,
            "user_id": str(user_id) if user_id else "anonymous",
            "source": source,
            "original_text": source,
            "output": output,
            "generated_text": output,
            "format": format_type,
            "transformation_type": format_type,
            "audience": audience,
            "tone": tone,
            "detail": detail,
            "title": title or f"{format_type} Deliverable",
            "provider": provider,
            "model": model,
            "words_input": len(source.split()),
            "words_output": len(output.split()),
            "created_at": now_iso
        }

        if self.ping():
            try:
                mongo_doc = dict(record)
                mongo_doc["_id"] = new_id
                self.db["transformations"].insert_one(mongo_doc)
            except Exception as e:
                logger.error("Failed to insert transformation to Mongo: %s", str(e))
                # Fallback to local
                data = self._read_fallback()
                data["transformations"].insert(0, record)
                self._write_fallback(data)
        else:
            data = self._read_fallback()
            data["transformations"].insert(0, record)
            self._write_fallback(data)

        return record

    def get_user_history(
        self,
        user_id: Optional[str],
        limit: int = 50,
        search_query: str = "",
        filter_type: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Retrieves user history with strict user isolation, optional search, and format filtering.
        """
        if not user_id:
            return []

        search_q = (search_query or "").strip().lower()
        filter_t = (filter_type or "").strip()

        if self.ping():
            try:
                query: Dict[str, Any] = {"user_id": str(user_id)}
                if filter_t and filter_t != "all":
                    query["$or"] = [
                        {"format": {"$regex": filter_t, "$options": "i"}},
                        {"transformation_type": {"$regex": filter_t, "$options": "i"}}
                    ]
                if search_q:
                    search_clause = [
                        {"title": {"$regex": search_q, "$options": "i"}},
                        {"output": {"$regex": search_q, "$options": "i"}},
                        {"source": {"$regex": search_q, "$options": "i"}}
                    ]
                    if "$or" in query:
                        query = {"$and": [{"user_id": str(user_id)}, {"$or": query["$or"]}, {"$or": search_clause}]}
                    else:
                        query["$or"] = search_clause

                cursor = self.db["transformations"].find(query).sort("created_at", DESCENDING).limit(limit)
                results = []
                for doc in cursor:
                    doc["id"] = str(doc.get("_id") or doc.get("id"))
                    results.append(doc)
                return results
            except Exception as e:
                logger.error("Error retrieving user history from Mongo: %s", str(e))

        # Fallback to local data
        data = self._read_fallback()
        all_items = [
            t for t in data.get("transformations", [])
            if str(t.get("user_id")) == str(user_id)
        ]
        filtered = []
        for t in all_items:
            fmt = str(t.get("format") or t.get("transformation_type") or "")
            if filter_t and filter_t != "all" and filter_t.lower() not in fmt.lower():
                continue
            if search_q:
                content_blob = (str(t.get("title", "")) + " " + str(t.get("output", "")) + " " + str(t.get("source", ""))).lower()
                if search_q not in content_blob:
                    continue
            t["id"] = str(t.get("_id") or t.get("id"))
            filtered.append(t)
        return filtered[:limit]

    def get_transformation_by_id(self, item_id: str, user_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """Ensures that users can only access their own saved transformation records."""
        if not item_id or not user_id:
            return None

        if self.ping():
            try:
                doc = self.db["transformations"].find_one({"_id": item_id, "user_id": str(user_id)})
                if not doc:
                    doc = self.db["transformations"].find_one({"id": item_id, "user_id": str(user_id)})
                if doc:
                    doc["id"] = str(doc.get("_id") or doc.get("id"))
                    return doc
            except Exception as e:
                logger.error("Error reading transformation by ID from Mongo: %s", str(e))

        data = self._read_fallback()
        for t in data.get("transformations", []):
            if (str(t.get("id")) == str(item_id) or str(t.get("_id")) == str(item_id)) and str(t.get("user_id")) == str(user_id):
                t["id"] = str(t.get("_id") or t.get("id"))
                return t
        return None

    def delete_transformation(self, item_id: str, user_id: Optional[str]) -> bool:
        """Deletes a single transformation belonging to the user."""
        if not item_id or not user_id:
            return False

        if self.ping():
            try:
                res = self.db["transformations"].delete_one({"_id": item_id, "user_id": str(user_id)})
                if res.deleted_count == 0:
                    res = self.db["transformations"].delete_one({"id": item_id, "user_id": str(user_id)})
                return res.deleted_count > 0
            except Exception as e:
                logger.error("Error deleting transformation in Mongo: %s", str(e))
                return False

        data = self._read_fallback()
        orig_len = len(data.get("transformations", []))
        data["transformations"] = [
            t for t in data.get("transformations", [])
            if not ((str(t.get("id")) == str(item_id) or str(t.get("_id")) == str(item_id)) and str(t.get("user_id")) == str(user_id))
        ]
        if len(data["transformations"]) < orig_len:
            self._write_fallback(data)
            return True
        return False

    def clear_user_history(self, user_id: Optional[str]) -> int:
        """Clears all transformation history for the given user."""
        if not user_id:
            return 0

        if self.ping():
            try:
                res = self.db["transformations"].delete_many({"user_id": str(user_id)})
                return res.deleted_count
            except Exception as e:
                logger.error("Error clearing user history in Mongo: %s", str(e))

        data = self._read_fallback()
        orig_len = len(data.get("transformations", []))
        data["transformations"] = [
            t for t in data.get("transformations", [])
            if str(t.get("user_id")) != str(user_id)
        ]
        deleted_count = orig_len - len(data["transformations"])
        self._write_fallback(data)
        return deleted_count

    def get_dashboard_stats(self, user_id: Optional[str]) -> Dict[str, Any]:
        """Calculates personalized usage statistics for the user dashboard."""
        if not user_id:
            return {
                "total_transformations": 0,
                "words_transformed": 0,
                "time_saved_hours": 0.0,
                "popular_formats": []
            }

        history = self.get_user_history(user_id, limit=200)
        total = len(history)
        words = sum(int(item.get("words_output") or 0) for item in history)
        # Average reading/writing speed saved ~200 wpm
        time_saved = round((words / 200) / 60, 1)

        format_counts: Dict[str, int] = {}
        for h in history:
            fmt = h.get("format") or h.get("transformation_type") or "General"
            format_counts[fmt] = format_counts.get(fmt, 0) + 1

        top_formats = sorted(format_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "total_transformations": total,
            "words_transformed": words,
            "time_saved_hours": time_saved,
            "popular_formats": top_formats,
            "recent_items": history[:5]
        }

# Global singleton
db = DatabaseManager()
