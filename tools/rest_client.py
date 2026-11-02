import argparse
import json
import sys

import httpx


def main():
    parser = argparse.ArgumentParser(description="Client fuer die Mock-Retouren-API")
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    commands = parser.add_subparsers(dest="command", required=True)
    listing = commands.add_parser("list")
    listing.add_argument("--status", choices=["REGISTERED", "RECEIVED", "INSPECTED"])
    listing.add_argument("--marketplace", choices=["AMAZON", "ZALANDO"])
    single = commands.add_parser("get")
    single.add_argument("return_id")
    order = commands.add_parser("order")
    order.add_argument("order_id")
    update = commands.add_parser("status")
    update.add_argument("return_id")
    update.add_argument("status", choices=["REGISTERED", "RECEIVED", "INSPECTED"])
    options = parser.parse_args()
    try:
        with httpx.Client(base_url=options.url, timeout=5, trust_env=False) as client:
            if options.command == "list":
                parameters = {name: getattr(options, name) for name in ("status", "marketplace") if getattr(options, name)}
                response = client.get("/api/v1/returns", params=parameters)
            elif options.command == "get":
                response = client.get("/api/v1/returns/" + options.return_id)
            elif options.command == "order":
                response = client.get("/api/v1/orders/" + options.order_id)
            else:
                response = client.patch("/api/v1/returns/" + options.return_id + "/status", json={"status": options.status})
            response.raise_for_status()
            print(json.dumps(response.json(), ensure_ascii=False, indent=2))
    except httpx.HTTPError as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
