from typing import Annotated

from pydantic.fields import Field
from pydantic.main import BaseModel

from sema4ai.actions import Response, action


class Row(BaseModel):
    cells: Annotated[list[str], Field(description="Row cells")]


class CustomResponse(BaseModel):
    ok: bool
    document_id: Annotated[
        str, Field(description="The ID of the document.", validation_alias="documentId")
    ]


@action(is_consequential=True)
def add_rows(header: Row = Row(cells=[])) -> Response[CustomResponse]:
    return Response(result=CustomResponse(ok=True, documentId="doc-id"))  # type: ignore
