from database.mongodb import workprogress_collection
doc = workprogress_collection.find_one()
print(doc)
