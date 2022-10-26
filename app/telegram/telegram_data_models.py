from typing import Optional, Dict

from pydantic import BaseModel, Field


class WebhookSettings(BaseModel):
    url: str
    secret_token: Optional[str]

    def dict(self, *args, exclude_none=True, **kwargs):
        return super().dict(*args, exclude_none=exclude_none, **kwargs)


class WebhookInfo(BaseModel):
    url: str
    has_custom_certificate: bool
    pending_update_count: int
    ip_address: Optional[str]
    last_error_date: Optional[int]
    last_error_message: Optional[str]
    last_synchronization_error_date: Optional[int]
    max_connections: Optional[int]
    allowed_updates: Optional[str]


class WebhookInfoReply(BaseModel):
    ok: bool
    result: WebhookInfo


class User(BaseModel):
    id: int
    is_bot: bool
    first_name: str
    language_code: str


class Chat(BaseModel):
    id: int
    first_name: str
    type: str


class Message(BaseModel):
    message_id: int
    from_: User = Field(..., alias='from')
    chat: Chat
    date: int
    text: Optional[str]
    animation: Optional[Dict]
    document: Optional[Dict]


class Update(BaseModel):
    update_id: int
    message: Optional[Message]
    edited_message: Optional[Message]


class OutMessage(BaseModel):
    chat_id: int
    text: str
    # parse_mode: str = 'MarkdownV2'
