from fastapi import APIRouter 
from strawberry.fastapi import GraphQLRouter
from app.core.schemas.graphql.schema import schema


@strawberry.type
class Query:
    @strawberry.field
    async def recommend_products(self, prefs: List[str]) -> List[Product]:
        return await Recommender.recommend_products(prefs)

    @strawberry.field
    async def recommend_courses(self, interests: List[str]) -> List[Course]:
        return await Recommender.recommend_courses(interests)

    @strawberry.field
    async def hybrid_recommendation(self, user_id: str) -> Recommendation:
        return await Recommender.hybrid_recommendation(user_id)

schema = strawberry.Schema(Query)


router_graphql = APIRouter()
graphql_app = GraphQLRouter(schema)
router_graphql.include_router(graphql_app, prefix="/graphql")