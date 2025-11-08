import strawberry
from .types import UserType, UserInput, MediaType, MediaInput
from .resolvers import Query

schema = strawberry.Schema(query=Query)