import pytest

from shtemplate import ExpansionError, expand


def test_plain_braced_reference_is_substituted() -> None:
    assert expand("${NAME}", {"NAME": "ada"}) == "ada"


def test_bare_reference_is_substituted() -> None:
    assert expand("hi $NAME!", {"NAME": "ada"}) == "hi ada!"


def test_unset_reference_expands_to_empty_by_default() -> None:
    assert expand("[${MISSING}]", {}) == "[]"


def test_empty_reference_is_kept_empty() -> None:
    assert expand("[${EMPTY}]", {"EMPTY": ""}) == "[]"


def test_colon_minus_uses_default_when_unset() -> None:
    assert expand("${X:-fallback}", {}) == "fallback"


def test_colon_minus_uses_default_when_empty() -> None:
    assert expand("${X:-fallback}", {"X": ""}) == "fallback"


def test_colon_minus_keeps_value_when_set() -> None:
    assert expand("${X:-fallback}", {"X": "set"}) == "set"


def test_minus_uses_default_only_when_unset() -> None:
    assert expand("${X-fallback}", {}) == "fallback"


def test_minus_keeps_empty_value() -> None:
    assert expand("${X-fallback}", {"X": ""}) == ""


def test_colon_plus_uses_alt_when_set_and_not_empty() -> None:
    assert expand("${X:+yes}", {"X": "v"}) == "yes"


def test_colon_plus_is_empty_when_empty() -> None:
    assert expand("${X:+yes}", {"X": ""}) == ""


def test_plus_uses_alt_when_set_even_if_empty() -> None:
    assert expand("${X+yes}", {"X": ""}) == "yes"


def test_plus_is_empty_when_unset() -> None:
    assert expand("${X+yes}", {}) == ""


def test_colon_question_raises_when_unset() -> None:
    with pytest.raises(ExpansionError, match="boom"):
        expand("${X:?boom}", {})


def test_colon_question_raises_when_empty() -> None:
    with pytest.raises(ExpansionError, match="boom"):
        expand("${X:?boom}", {"X": ""})


def test_question_keeps_empty_value() -> None:
    assert expand("${X?boom}", {"X": ""}) == ""


def test_question_without_message_has_default_text() -> None:
    with pytest.raises(ExpansionError, match="parameter null or not set"):
        expand("${X:?}", {})


def test_double_dollar_is_a_literal_dollar() -> None:
    assert expand("price $$5 ${N}", {"N": "now"}) == "price $5 now"


def test_trailing_dollar_is_literal() -> None:
    assert expand("ends with $", {}) == "ends with $"


def test_dollar_before_non_name_is_literal() -> None:
    assert expand("$ money", {}) == "$ money"


def test_strict_raises_on_unset_plain_reference() -> None:
    with pytest.raises(ExpansionError, match="undefined variable: X"):
        expand("${X}", {}, strict=True)


def test_strict_still_honours_default_operator() -> None:
    assert expand("${X:-ok}", {}, strict=True) == "ok"


def test_missing_closing_brace_raises() -> None:
    with pytest.raises(ExpansionError, match="unterminated"):
        expand("${X", {"X": "v"})


def test_empty_braces_raise() -> None:
    with pytest.raises(ExpansionError, match="invalid variable name"):
        expand("${}", {})


def test_unknown_operator_raises() -> None:
    with pytest.raises(ExpansionError, match="unknown operator"):
        expand("${X@y}", {"X": "v"})


def test_default_word_is_expanded_like_the_shell() -> None:
    assert expand("${X:-$HOME/bin}", {"HOME": "/h"}) == "/h/bin"


def test_env_defaults_to_empty_mapping() -> None:
    assert expand("${X:-d}") == "d"
