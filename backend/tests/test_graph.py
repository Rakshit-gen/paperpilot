from paperpilot.graph import grade_node, route_after_grade


def test_route_after_grade_relevant():
    assert route_after_grade({"is_relevant": True}) == "generate_answer"


def test_route_after_grade_not_relevant():
    assert route_after_grade({"is_relevant": False}) == "insufficient_context"


def test_grade_node_short_circuits_on_empty_retrieval():
    # no groq call should happen here, empty retrieval is decided locally
    result = grade_node({"retrieved": [], "question": "anything"})
    assert result == {"is_relevant": False}
