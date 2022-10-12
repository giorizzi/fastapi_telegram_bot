from typing import List, Dict

from httpx import AsyncClient
from pydantic import BaseModel

NGROK_URL = 'http://ngrok:4040'


class Config(BaseModel):
    addr: str
    inspect: bool


class Tunnel(BaseModel):
    name: str
    uri: str
    public_url: str
    proto: str
    config: Config
    metrics: Dict


class Tunnels(BaseModel):
    tunnels: List[Tunnel]
    uri: str


async def get_public_url(client: AsyncClient):
    r = await client.get(NGROK_URL + '/api/tunnels')
    ngrok_info = Tunnels.parse_raw(r.text)
    active_tunnel = next(filter(lambda x: x.config.addr.endswith('app:80') and x.proto == 'https', ngrok_info.tunnels))
    assert active_tunnel
    return active_tunnel.public_url
