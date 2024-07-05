import datetime
import typing
from contextlib import contextmanager
from typing import Iterator, Optional, Union

from starlette.requests import Request
from starlette.responses import Response

if typing.TYPE_CHECKING:
    from sema4ai.action_server._database import Database
    from sema4ai.action_server._models import UserSession

# Expected value in session data: isodate formatted string.
KEY_CREATED_AT = "created-at"

# Expected value in session data: boolean determining whether this uuid was requested
# externally or generated internally automatically.
KEY_EXTERNAL = "external"

# Expected value in session data: isodate formatted string.
KEY_ACCESSED_AT = "accessed-at"

# The name of the cookie with the automatically generated session id.
COOKIE_SESSION_ID = "action-server-session-id"


def get_current_time_as_iso() -> str:
    return datetime_to_iso(datetime.datetime.now())


def datetime_to_iso(d: datetime.datetime | float) -> str:
    """
    Accepts a datetime or a float with seconds from epoch.
    """
    if isinstance(d, float):
        d = datetime.datetime.fromtimestamp(d)
    return d.isoformat()


def iso_to_datetime(isostr: str) -> datetime.datetime:
    return datetime.datetime.fromisoformat(isostr)


def create_user_session(external: bool) -> "UserSession":
    """
    Args:
        external: when True this session id will allow authentication
            tokens to be queried (other sessions don't allow external
            clients to request the actual token).
    """
    from sema4ai.action_server._models import UserSession, get_db

    db = get_db()
    with db.connect():
        import uuid

        session_id = str(uuid.uuid4())

        while True:
            try:
                db.first(
                    UserSession, "SELECT * FROM user_session WHERE id = ?", [session_id]
                )
            except KeyError:
                break  # Ok, it's not there
            else:
                # Although almost impossible, theoretically we could have a conflict,
                # so, generate a new one if that's the case.
                session_id = str(uuid.uuid4())

        current_time = get_current_time_as_iso()

        with db.transaction():
            created = UserSession(
                id=session_id,
                created_at=current_time,
                accessed_at=current_time,
                external=external,
            )
            db.insert(created)

        return created


def _get_user_session_from_id(
    session_id: str, db: "Database"
) -> "Optional[UserSession]":
    from sema4ai.action_server._models import UserSession

    try:
        return db.first(
            UserSession, "SELECT * FROM user_session WHERE id = ?", [session_id]
        )
    except KeyError:
        return None


def _get_session_id(request: Request) -> str:
    from sema4ai.action_server._models import get_db

    db = get_db()
    with db.connect(), db.transaction():
        session_id = request.cookies.get(COOKIE_SESSION_ID)
        if not session_id:
            session_id = create_user_session(external=False).id
        else:
            # There is a session id in the request. Let's check if it's still
            # valid.
            user_session = _get_user_session_from_id(session_id, db)
            if user_session is None:
                # Cookie is there, but the session isn't in the db, we need to
                # create a new one.
                session_id = create_user_session(external=False).id
            else:
                accessed_at = iso_to_datetime(user_session.accessed_at)
                now = datetime.datetime.now()

                if now > (accessed_at + datetime.timedelta(days=7)):
                    created_at = iso_to_datetime(user_session.created_at)
                    if now > (created_at + datetime.timedelta(days=30)):
                        # It was created more than a month ago and it wasn't
                        # accessed in 7 days already: automatically remove
                        # the session.

                        # We don't use DELETE CASCADE, so, do it one by one at this point.
                        db.execute(
                            "DELETE FROM temp_user_session_data WHERE user_session_id = ?",
                            [session_id],
                        )
                        db.execute(
                            "DELETE FROM oauth2 WHERE user_session_id = ?",
                            [session_id],
                        )
                        db.execute(
                            "DELETE FROM user_session WHERE id = ?", [session_id]
                        )

                        session_id = create_user_session(external=False).id

    return session_id


def _set_session_id(response: Response, session_id: str) -> None:
    ONE_DAY = 60 * 60 * 24
    TWO_WEEKS = ONE_DAY * 14
    response.set_cookie(COOKIE_SESSION_ID, session_id, max_age=TWO_WEEKS)


JSONValue = Union[
    dict[str, "JSONValue"], list["JSONValue"], str, int, float, bool, None
]


def _set_session_data(
    session_id: str, key: str, value: JSONValue, expires_at: datetime.datetime
) -> None:
    import json

    from sema4ai.action_server._models import TempUserSessionData, get_db

    db = get_db()
    with db.connect(), db.transaction():
        db.insert_or_update(
            TempUserSessionData(
                user_session_id=session_id,
                key=key,
                data=json.dumps(value),
                expires_at=datetime_to_iso(expires_at),
            ),
            keys=["user_session_id", "key"],
        )


def _get_session_data(session_id: str, key: str) -> JSONValue:
    import json

    from sema4ai.action_server._models import TempUserSessionData, get_db

    db = get_db()
    with db.connect(), db.transaction():
        try:
            found = db.first(
                TempUserSessionData,
                "SELECT * FROM temp_user_session_data WHERE user_session_id = ? AND key = ?",
                [session_id, key],
            )
        except KeyError:
            return None
        else:
            expires_at = found.expires_at
            if datetime.datetime.now() > iso_to_datetime(expires_at):
                # Expired
                db.delete(found, ["session_id", "key"])
                return None

            return json.loads(found.data)


class _BaseScopeContext:
    def __init__(self, session_id: str):
        self.session_id = session_id

    def set_session_data(
        self, key: str, value: JSONValue, expires_at: datetime.datetime
    ) -> None:
        _set_session_data(self.session_id, key, value, expires_at)

    def get_session_data(self, key: str) -> JSONValue:
        return _get_session_data(self.session_id, key)


class ReferencedScopeContext(_BaseScopeContext):
    def __init__(self, session_id: str, create: bool):
        super().__init__(session_id=session_id)
        assert not create, "TODO: Handle creation"


class SessionScopeContext(_BaseScopeContext):
    def __init__(self, request: Request):
        super().__init__(_get_session_id(request))
        self.request = request
        self._response: Optional[Response] = None

    @property
    def response(self) -> Optional[Response]:
        return self._response

    @response.setter
    def response(self, response: Response):
        _set_session_id(response, self.session_id)
        self._response = response


@contextmanager
def session_scope(request: Request) -> Iterator[SessionScopeContext]:
    scope = SessionScopeContext(request)
    yield scope
    assert (
        scope.response is not None
    ), "The response must be set to set the cookie (if it was just created)."


@contextmanager
def referenced_session_scope(
    reference_id: str, create: bool
) -> Iterator[ReferencedScopeContext]:
    scope = ReferencedScopeContext(reference_id, create=create)

    yield scope
