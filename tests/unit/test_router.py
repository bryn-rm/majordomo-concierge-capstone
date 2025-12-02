from src.orchestration.router import route
from src.orchestration.graph import FlowName


def test_route_diary_capture():
    d = route("Log: this is a diary entry")
    assert d.flow == FlowName.DIARY_CAPTURE

    d2 = route("note: remember to breathe")
    assert d2.flow == FlowName.DIARY_CAPTURE


def test_route_diary_reflection():
    d = route("What have I been saying about work lately?")
    assert d.flow == FlowName.DIARY_REFLECTION

    d2 = route("Show me patterns in my notes")
    assert d2.flow == FlowName.DIARY_REFLECTION


def test_route_smart_home():
    d = route("Turn the lights off and lock the door.")
    assert d.flow == FlowName.SMART_HOME


def test_route_default_knowledge():
    d = route("Who was Ada Lovelace?")
    assert d.flow == FlowName.KNOWLEDGE
