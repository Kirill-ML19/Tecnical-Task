from typing import TypedDict

class Post(TypedDict):
    userId: int
    id: int
    title: str
    body: str