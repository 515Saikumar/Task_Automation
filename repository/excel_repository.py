from bson.binary import Binary
from datetime import datetime
from bson.objectid import ObjectId # Added missing import

from database.mongodb import tasks_collection 

# Changed from TaskRepository to ExcelRepository to match your API
class ExcelRepository:

    @staticmethod
    def save_excel(filename, content_type, file_bytes):

        document = {
            "filename": filename,
            "content_type": content_type,
            "file_data": Binary(file_bytes),
            "uploaded_at": datetime.utcnow(),
            "status": "Uploaded"
        }

        # Changed excel_collection to tasks_collection
        result = tasks_collection.insert_one(document)

        return str(result.inserted_id)

    @staticmethod
    def delete_excel(file_id: str):
        # Changed excel_collection to tasks_collection
        result = tasks_collection.delete_one({"_id": ObjectId(file_id)})
        return result.deleted_count > 0