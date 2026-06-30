from pydantic import BaseModel


class RepositoryChatRequest(BaseModel):
    repo_path: str
    question: str


class RepositoryChatResponse(BaseModel):
    answer: str