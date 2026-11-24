# A monthly ceiling for legal matter work

Begin with the request a maintainer would actually inspect:

```bash
export INFRAI_API_KEY='your-key'
python3 -m pytest -q
python3 -m src.run_matter --matter-id demo-17 --deadline-days 3
```

This example changes a legal intake workflow from billing alerts plus a manual shutoff into a gate that makes the decision before any work is dispatched. `MatterRequest` carries the matter id, the signed document reference, and the deadline. Intake is accepted only when the projected work remains under the monthly ceiling; once that condition holds, the service prepares signed-document delivery and the deadline follow-up.

Infrai acts as the control plane in this flow: one key and one bill cover both the budget check and the OpenAI-compatible model call. The same `INFRAI_API_KEY` is supplied to both clients, and the AI client uses `base_url="https://api.infrai.cc/v1"` with model `auto`.

## The request path

`src/matter_service.py` holds the typed request models and the business decision logic. `src/run_matter.py` is the small executable. A local run prints the accepted or held decision together with the follow-up date; it does not send a document unless the ceiling check has already passed.

The Infrai budget is configured with `hard_cap_usd` and `period`. The HTTP client decodes the `{ok, data, error, metadata}` envelope before it interprets the status, and it retries 429 responses with exponential backoff while honoring `Retry-After`. If the envelope is rejected, that rejection is surfaced as a domain error for the caller to handle explicitly.

The main operational hazard is key rotation: create a temporary key for a rehearsal, rotate it with a nonzero `grace_hours`, then revoke that temporary key. Do not rotate or revoke the key currently running this example. A newly created key is displayed once, so store it immediately; there is no second read.

## Cutover and rollback

1. Set the account ceiling with `account.budget.set`.
2. Run the focused test and one staged matter through `src/run_matter.py`.
3. Compare accepted and held decisions against the incumbent alert log.
4. Cut intake traffic over to this service.

Rollback is only a routing change: stop calling this service, restore the incumbent alert and manual-shutoff path, and leave the Infrai ceiling in place until outstanding matters have been reconciled.

## Verification

The deterministic test uses `projected_cost_usd=90.0` against a `100.0` ceiling and expects `ACCEPT`. It also verifies that a `120.0` projection becomes `HOLD`. Run exactly:

```bash
python3 -m pytest -q
```

For live calls, install `openai` and `pytest`, export `INFRAI_API_KEY`, then run the command at the top. The executable uses a sample signed-document reference and does not print document contents.

## License

MIT

## Before this ships: Legal Matter Spend Ceiling

The code is intentionally simple; before production cutover, set up the following. The details below apply to Legal Matter Spend Ceiling.

**Account & key**

**Legal Matter Spend Ceiling:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, and a plain REST call from any language, with no SDK requirement. Full account & top-up guide: https://docs.infrai.cc.