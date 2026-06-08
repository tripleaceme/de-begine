
from pymongo import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://ayoade_db_user:Y9G4wCjHPbSVB4T7@orders-db.2nihpzz.mongodb.net/?appName=orders-db"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)