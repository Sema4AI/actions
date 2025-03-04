from pydantic import BaseModel, Field


class RepositoryInfo(BaseModel):
    owner_id: str = Field(description="The owner of the repository")
    name: str = Field(description="The name of the repository")


class CreateIssueData(BaseModel):
    title: str = Field(description="The title of the issue")
    body: str = Field(description="The body of the issue")
