import argparse
import json
import sys
from pathlib import Path

import grpc
from google.protobuf.json_format import MessageToJson, ParseDict, ParseError

from shopeasy.generated import article_condition_service_pb2 as article
from shopeasy.generated import article_condition_service_pb2_grpc as article_grpc


def main():
    parser = argparse.ArgumentParser(description="gRPC-Client fuer die ShopEasy-Artikelbewertung")
    parser.add_argument("--target",default="127.0.0.1:50051")
    commands = parser.add_subparsers(dest="command",required=True)
    check = commands.add_parser("check")
    check.add_argument("return_id")
    check.add_argument("sku")
    check.add_argument("observed_condition", choices=["AS_NEW", "MINOR_WEAR", "VISIBLY_WORN", "DAMAGED", "MISSING_TAGS", "MISSING_PARTS"])
    check.add_argument("--tags-present", action="store_true")
    check.add_argument("--original-packaging", action="store_true")
    check.add_argument("--note", default="")
    check.add_argument("--inspected-at", default="")
    check.add_argument("--image-url", action="append", default=[])
    result = commands.add_parser("result")
    result.add_argument("return_id")
    result.add_argument("sku")
    batch = commands.add_parser("batch")
    batch.add_argument("file", type=Path)
    options = parser.parse_args()
    with grpc.insecure_channel(options.target) as channel:
        article_client = article_grpc.ArticleConditionServiceStub(channel)
        try:
            if options.command == "check":
                response = article_client.CheckCondition(article.ConditionCheckRequest(return_id=options.return_id, sku=options.sku, observed_condition=article.ObservedCondition.Value(options.observed_condition), tags_present=options.tags_present, original_packaging=options.original_packaging, inspector_note=options.note, inspected_at=options.inspected_at, image_urls=options.image_url), timeout=5)
            elif options.command == "result":
                response = article_client.GetCheckResult(article.GetCheckResultRequest(return_id=options.return_id, sku=options.sku), timeout=5)
            else:
                request = ParseDict(json.loads(options.file.read_text(encoding="utf-8")), article.ConditionCheckBatchRequest())
                response = article_client.CheckConditionBatch(request, timeout=5)
            print(MessageToJson(response,preserving_proto_field_name=True))
        except grpc.RpcError as error:
            print(f"{error.code().name}: {error.details()}",file=sys.stderr)
            return 1
        except (OSError, ValueError, ParseError) as error:
            print(str(error), file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
