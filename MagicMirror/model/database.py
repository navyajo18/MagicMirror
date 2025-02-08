from pymongo import MongoClient

client = MongoClient('localhost', 27017)  # Connects to the MongoDB server running on localhost
db = client['virtual_try_on']  # Use or create a database called 'virtual_try_on'
clothing_collection = db.clothing  # Use or create a collection called 'clothing'

def save_clothing_item(type, image_path):
    clothing_item = {
        'type': type,
        'image_path': image_path
    }
    clothing_collection.insert_one(clothing_item)

# Example of saving an item
save_clothing_item('shirt', 'path/to/shirts/shirt1.png')


def get_clothing_by_type(type):
    return list(clothing_collection.find({'type': type}))

# Example usage
shirts = get_clothing_by_type('shirt')
for shirt in shirts:
    print(shirt)
