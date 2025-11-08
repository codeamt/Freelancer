from fastapi import APIRouter 
from strawberry.fastapi import GraphQLRouter
from app.core.schemas.graphql.schema import schema

router_graphql = APIRouter()
graphql_app = GraphQLRouter(schema)
router_graphql.include_router(graphql_app, prefix="/graphql")