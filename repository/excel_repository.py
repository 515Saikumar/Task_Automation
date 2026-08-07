import hashlib
from bson.binary import Binary
from datetime import datetime, timezone, timedelta
from bson.objectid import ObjectId
from database.mongodb import tasks_collection 

class ExcelRepository:

    @staticmethod
    def save_excel(filename, content_type, file_bytes):
        # Generate a unique fingerprint (hash) of the file content
        file_hash = hashlib.md5(file_bytes).hexdigest()
        
        # --- THE FIX: Lock the IST offset directly into an ISO string ---
        ist_tz = timezone(timedelta(hours=5, minutes=30))
        upload_time = datetime.now(ist_tz).isoformat()
        # ----------------------------------------------------------------

        document = {
            "filename": filename,
            "content_type": content_type,
            "file_data": Binary(file_bytes),
            "uploaded_at": upload_time,  # <-- Using our strictly formatted IST string here!
            "status": "Uploaded",
            "task_hash": file_hash  
        }
        
        try:
            result = tasks_collection.insert_one(document)
            return str(result.inserted_id)
        except Exception as e:
            # If MongoDB throws a DuplicateKeyError, it means this exact file was already uploaded
            if "E11000 duplicate key error" in str(e):
                raise Exception("This exact Excel file has already been uploaded.")
            raise e

    @staticmethod
    def delete_excel(file_id: str):
        result = tasks_collection.delete_one({"_id": ObjectId(file_id)})
        return result.deleted_count > 0