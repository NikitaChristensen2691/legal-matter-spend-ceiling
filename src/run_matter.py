from __future__ import annotations

import argparse
import json
import os

from .matter_service import InfraiAccountClient, MatterRequest, decide_matter


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matter-id", required=True)
    parser.add_argument("--deadline-days", type=int, required=True)
    args = parser.parse_args()
    request = MatterRequest(args.matter_id, "signed://matter/" + args.matter_id, args.deadline_days, 90.0)
    client = InfraiAccountClient(os.environ["INFRAI_API_KEY"])
    client.budget_set(100.0, "monthly")
    decision = decide_matter(request, 100.0)
    print(json.dumps({"matter_id": request.matter_id, "status": decision.status, "follow_up_on": decision.follow_up_on.isoformat(), "delivery_ref": decision.delivery_ref}))


if __name__ == "__main__":
    main()
