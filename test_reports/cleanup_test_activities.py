import asyncio, os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import dotenv_values

env = dotenv_values("/app/backend/.env")

async def main():
    c = AsyncIOMotorClient(env["MONGO_URL"])
    db = c[env["DB_NAME"]]
    acts = await db.collection_activity.find({"nomor_kontrak": {"$regex": "^TEST_"}}).to_list(100)
    ids = [str(a["_id"]) for a in acts]
    print("found", ids)
    r1 = await db.collection_activity_photos.delete_many({"collection_activity_id": {"$in": ids}})
    r2 = await db.collection_activity.delete_many({"nomor_kontrak": {"$regex": "^TEST_"}})
    print("photos deleted", r1.deleted_count, "activities deleted", r2.deleted_count)

asyncio.run(main())
