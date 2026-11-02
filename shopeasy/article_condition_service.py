from datetime import datetime

import grpc
from google.protobuf.json_format import MessageToDict

from .generated import article_condition_service_pb2 as messages
from .generated import article_condition_service_pb2_grpc as services
from .storage import DomainError


def validate_identity(return_id, sku):
    if not return_id.strip() or not sku.strip() or len(return_id) > 100 or len(sku) > 100:
        raise DomainError("INVALID_ARGUMENT", "return_id und sku mit jeweils 1 bis 100 Zeichen erforderlich.")


def evaluate(request):
    validate_identity(request.return_id, request.sku)
    if request.observed_condition not in (messages.AS_NEW, messages.MINOR_WEAR, messages.VISIBLY_WORN, messages.DAMAGED, messages.MISSING_TAGS, messages.MISSING_PARTS):
        raise DomainError("INVALID_ARGUMENT", "Gueltiger observed_condition erforderlich.")
    if len(request.inspector_note) > 500:
        raise DomainError("INVALID_ARGUMENT", "Notiz darf maximal 500 Zeichen enthalten.")
    if request.inspected_at:
        try:
            timestamp = datetime.fromisoformat(request.inspected_at.replace("Z", "+00:00"))
            if timestamp.tzinfo is None:
                raise ValueError()
        except ValueError:
            raise DomainError("INVALID_ARGUMENT", "inspected_at muss ein ISO-8601-Zeitstempel mit Zeitzone sein.") from None
    if request.observed_condition in (messages.DAMAGED, messages.VISIBLY_WORN):
        decision, confidence, reason = messages.REJECT, 0.95, "Beschaedigter oder deutlich getragener Artikel."
    elif request.observed_condition == messages.AS_NEW and request.tags_present and request.original_packaging:
        decision, confidence, reason = messages.ACCEPT, 0.95, "Neuwertig, Etiketten und Originalverpackung vorhanden."
    else:
        decision, confidence, reason = messages.MANUAL_REVIEW, 0.6, "Grenzfall: Gebrauchsspuren oder fehlende Etiketten, Verpackung oder Teile."
    payload = MessageToDict(request, preserving_proto_field_name=True, always_print_fields_with_no_presence=True)
    recommendation = {"decision": decision, "confidence_score": confidence, "reason": reason, "requires_manual_review": decision == messages.MANUAL_REVIEW}
    return payload, recommendation


class ArticleConditionService(services.ArticleConditionServiceServicer):
    def __init__(self, store):
        self.store = store

    def execute(self, context, operation):
        try:
            return operation()
        except DomainError as error:
            codes = {"INVALID_ARGUMENT": grpc.StatusCode.INVALID_ARGUMENT, "NOT_FOUND": grpc.StatusCode.NOT_FOUND, "ALREADY_EXISTS": grpc.StatusCode.ALREADY_EXISTS}
            context.abort(codes[error.kind], str(error))

    def CheckCondition(self, request, context):
        return self.execute(context, lambda: messages.ConditionCheckResponse(**self.store.check_articles([evaluate(request)])[0]))

    def CheckConditionBatch(self, request, context):
        def check_batch():
            if not request.items or len(request.items) > 100:
                raise DomainError("INVALID_ARGUMENT", "Ein Stapel muss 1 bis 100 Artikel enthalten.")
            checks = [evaluate(item) for item in request.items]
            return messages.ConditionCheckBatchResponse(results=[messages.ConditionCheckResponse(**result) for result in self.store.check_articles(checks)])
        return self.execute(context, check_batch)

    def GetCheckResult(self, request, context):
        def get_result():
            validate_identity(request.return_id, request.sku)
            return messages.ConditionCheckResponse(**self.store.get_check(request.return_id, request.sku))
        return self.execute(context, get_result)
