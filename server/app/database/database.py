"""
MongoDB Atlas Database Connection Manager.
Handles async connection creation, ping verification on startup, and connection cleanup on shutdown.
Automatically escapes special characters in database credentials according to RFC 3986.
"""

import urllib.parse
import pymongo.errors
from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings
from app.utils.logger import logger

# Global Motor client and database objects
db_client: AsyncIOMotorClient = None
db = None


def sanitize_mongodb_uri(uri: str) -> str:
    """
    Sanitizes MongoDB URI by URL-encoding special characters in username and password.
    Prevents PyMongo InvalidURI errors when passwords contain characters like @, #, !, $, etc.
    """
    if not uri or "://" not in uri:
        return uri
    
    scheme, remainder = uri.split("://", 1)
    if "@" not in remainder:
        return uri

    host_part = remainder
    query_part = ""
    if "?" in remainder:
        host_part, query_part = remainder.split("?", 1)
        query_part = "?" + query_part

    # Split at the last '@' which separates user credentials from host
    if "@" in host_part:
        userinfo, host = host_part.rsplit("@", 1)
        if ":" in userinfo:
            username, password = userinfo.split(":", 1)
            raw_user = urllib.parse.unquote(username)
            raw_pass = urllib.parse.unquote(password)
            encoded_user = urllib.parse.quote_plus(raw_user)
            encoded_pass = urllib.parse.quote_plus(raw_pass)
            return f"{scheme}://{encoded_user}:{encoded_pass}@{host}{query_part}"

    return uri


async def connect_to_mongo():
    """
    Establishes connection to MongoDB Atlas.
    Pings the database to confirm connectivity and seeds default demo accounts.
    Stops startup if connection fails.
    """
    global db_client, db

    raw_uri = settings.MONGODB_URI
    database_name = settings.DATABASE_NAME

    if not raw_uri:
        error_msg = "MONGODB_URI is not set in environment settings. Please check your .env file."
        logger.error(f"❌ Connection Failed: {error_msg}")
        print(f"\nMongoDB Connection Error: {error_msg}\n")
        raise RuntimeError(error_msg)

    # Automatically sanitize and URL-encode username and password for RFC 3986 compliance
    mongodb_uri = sanitize_mongodb_uri(raw_uri)

    try:
        # Create asynchronous Motor client for MongoDB Atlas
        db_client = AsyncIOMotorClient(mongodb_uri)
        db = db_client[database_name]

        # Send a ping command to verify connection
        await db_client.admin.command("ping")
        
        # Log and print success message as required
        logger.info("Database connected successfully.")
        print("\nMongoDB Atlas Connected Successfully\n")

        # Automatically seed default demo Candidate & Recruiter users
        from app.database.seeder import seed_default_users
        await seed_default_users()

    except pymongo.errors.OperationFailure as e:
        error_msg = (
            "Authentication Failed! Invalid MongoDB Atlas username or password.\n"
            "Please check:\n"
            "1. Go to MongoDB Atlas (https://cloud.mongodb.com) -> Security -> Database Access\n"
            "2. Verify your Database User username and password match MONGODB_URI in your .env file\n"
            "3. Ensure the user has read/write permissions to the database"
        )
        logger.error(f"❌ MongoDB Atlas Auth Error: {error_msg}")
        print(f"\nMongoDB Atlas Connection Error:\n{error_msg}\n")
        raise RuntimeError("MongoDB Authentication Failed: Check your username and password in .env") from e

    except Exception as e:
        error_details = str(e)
        logger.error(f"❌ Failed to connect to MongoDB Atlas: {error_details}")
        print(f"\nMongoDB Connection Error: {error_details}\n")
        raise RuntimeError(f"MongoDB Connection Failed: {error_details}") from e


async def close_mongo_connection():
    """
    Closes MongoDB client connection during application shutdown.
    """
    global db_client
    if db_client:
        db_client.close()
        logger.info("MongoDB connection closed.")
        print("MongoDB Connection Closed")


def get_database():
    """
    Helper function to access the active database instance.
    """
    return db
