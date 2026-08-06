from bson.binary import Binary
from datetime import datetime

from database.mongodb import tasks_collection 

class TaskRepository:

    @staticmethod
    def save_excel(filename, content_type, file_bytes):

        document = {

            "filename": filename,

            "content_type": content_type,

            "file_data": Binary(file_bytes),

            "uploaded_at": datetime.utcnow(),

            "status": "Uploaded"

        }

        result = excel_collection.insert_one(document)

        return str(result.inserted_id)

    # --- ADDED: Delete method ---
    @staticmethod
    def delete_excel(file_id: str):
        result = excel_collection.delete_one({"_id": ObjectId(file_id)})
        return result.deleted_count > 0