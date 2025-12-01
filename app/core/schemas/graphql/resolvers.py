import strawberry
from core.services.db import DBService
from core.services.recommender import Recommender
from typing import List

@strawberry.type
class Query:
    @strawberry.field
    async def recommend_products(self, user_id: str) -> List[str]:
        mongo = DBService.mongo()
        user = await mongo.users.find_one({"_id": user_id})
        prefs = user.get("preferences", [])
        return Recommender.recommend_products(prefs)

    @strawberry.field
    async def recommend_courses(self, interests: List[str]) -> List[str]:
        return Recommender.recommend_courses(interests)

schema = strawberry.Schema(query=Query)