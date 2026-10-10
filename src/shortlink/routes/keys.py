from dataclasses import asdict

from fastapi import APIRouter, Response

from shortlink.routes.deps import CurrentUser, ServicesDep
from shortlink.routes.schemas import ApiKeyIn, ApiKeyOut, NewApiKeyOut

router = APIRouter(prefix="/api/keys", tags=["api keys"])


@router.get("", response_model=list[ApiKeyOut])
def list_keys(user: CurrentUser, services: ServicesDep):
    return [ApiKeyOut(**asdict(key)) for key in services.auth.list_keys(user.id)]


@router.post("", response_model=NewApiKeyOut, status_code=201)
def create_key(body: ApiKeyIn, user: CurrentUser, services: ServicesDep):
    key, raw_key = services.auth.create_key(user.id, body.name)
    return NewApiKeyOut(**asdict(key), key=raw_key)


@router.delete("/{key_id}", status_code=204)
def revoke_key(key_id: int, user: CurrentUser, services: ServicesDep):
    services.auth.revoke_key(user.id, key_id)
    return Response(status_code=204)
