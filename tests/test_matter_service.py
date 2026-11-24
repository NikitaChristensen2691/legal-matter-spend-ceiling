from src.matter_service import MatterRequest, decide_matter


def test_ceiling_controls_delivery_and_follow_up() -> None:
    accepted = MatterRequest("m-1", "signed://m-1", 3, 90.0)
    held = MatterRequest("m-2", "signed://m-2", 3, 120.0)

    accepted_result = decide_matter(accepted, 100.0)
    held_result = decide_matter(held, 100.0)

    assert accepted_result.status == "ACCEPT"
    assert accepted_result.delivery_ref == "signed://m-1"
    assert held_result.status == "HOLD"
    assert held_result.delivery_ref == "not-sent"
