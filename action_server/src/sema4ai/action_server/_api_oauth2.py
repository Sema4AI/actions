from fastapi.routing import APIRouter
from starlette.responses import HTMLResponse

oauth2_api_router = APIRouter(prefix="/oauth2")


@oauth2_api_router.get("/redirect")
async def oauth2_redirect(
    code: str = "", state: str = "", scope: str = ""
) -> HTMLResponse:
    return HTMLResponse(
        """
<html>
<body>
OAuth2 authentication complete.<br/>
<br/>
Please wait, this window should be closed shortly...<br/>
<br/>
If it's not closed automatically, something unexpected happened. <br/>
In this case, please close this window and restart the login.<br/>
<br/>

    <script>
        window.opener.finishOAuth2({ 
        url: `${window.location.protocol}//${window.location.host}/${window.location.search}`,
        code: %(code)r,
        state: %(state)r,
        scope: %(scope)r,
        });
    </script>
    
</body>
</html>
"""
        % dict(code=code, state=state, scope=scope)
    )
