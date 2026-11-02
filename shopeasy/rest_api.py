from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ConfigDict

from .storage import DomainError


class ReturnView(BaseModel):
    return_id: str
    marketplace: Literal["AMAZON", "ZALANDO"]
    external_return_id: str
    order_id: str
    sku: str
    quantity: int
    reason: str
    status: Literal["REGISTERED", "RECEIVED", "INSPECTED"]
    created_at: str


class StatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["REGISTERED", "RECEIVED", "INSPECTED"]


def create_app(store, messaging):
    app = FastAPI(title="ShopEasy Sprint 2 - Mock Retouren-API",version="1.0.0",description="Simulierte Amazon-/Zalando-Retouren. Keine Verbindung zu echten Marktplatzkonten.")

    def translate(error):
        return HTTPException({"NOT_FOUND":404,"CONFLICT":409,"INVALID_ARGUMENT":422}[error.kind], detail=str(error))

    @app.get("/",include_in_schema=False)
    def index():
        return RedirectResponse("/docs")

    @app.get("/health")
    def health():
        return {"service":"shopeasy-sprint2","broker_connected":messaging.publisher_connected,"consumer_connected":messaging.consumer_connected,"pending_events":store.pending_count(),"received_message_count":messaging.received_count,"duplicate_message_count":messaging.duplicate_count}

    @app.get("/api/v1/returns")
    def list_returns(status: Literal["REGISTERED", "RECEIVED", "INSPECTED"] | None = None, marketplace: Literal["AMAZON", "ZALANDO"] | None = None):
        return {"data": store.list_returns(status, marketplace)}

    @app.get("/api/v1/orders/{order_id}")
    def get_order(order_id: str):
        try:
            return store.order(order_id)
        except DomainError as error:
            raise translate(error) from error

    @app.patch("/api/v1/returns/{return_id}/status",response_model=ReturnView)
    def update_status(return_id: str, payload: StatusUpdate):
        try:
            return store.update_status(return_id, payload.status)
        except DomainError as error:
            raise translate(error) from error

    @app.get("/api/v1/returns/{return_id}",response_model=ReturnView)
    def get_return(return_id: str):
        try:
            return store.get(return_id)
        except DomainError as error:
            raise translate(error) from error

    @app.get("/api/v1/status-updates")
    def status_updates(return_id: str | None = None):
        if return_id:
            try:
                store.get(return_id)
            except DomainError as error:
                raise translate(error) from error
        return {"transport":"RabbitMQ/AMQP 0-9-1","events":store.events(return_id)}

    return app
