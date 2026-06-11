"""
MongoDB Atlas configuration.

Importing this module only requires MongoDB env vars — it does NOT
touch Postgres or MinIO, so a job that only talks to Mongo never has
to provide unrelated credentials.
"""

import os

from config import env  # noqa: F401  (loads .env once, for its side effect)

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise EnvironmentError("MONGO_URI is not set. Provide your MongoDB Atlas connection string in .env")

MONGO_DB = os.getenv("MONGO_DB")

MONGO_COLLECTIONS = {
    "customers": "customers",
    "products": "products",
    "orders": "orders",
}
