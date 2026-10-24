from ollama.prompt_handler import describe_message, parse_reply, split_examples

PERSONA = """You are Mistress.

Rules:
1. Be short.

Examples:
- User says "hello" -> you reply "Introduce yourself."
- User says "are you an AI?" -> you reply "Lol, fuck off."
"""


def test_split_examples_moves_examples_into_turns():
    system, examples = split_examples(PERSONA)
    assert system == "You are Mistress.\n\nRules:\n1. Be short."
    assert examples == [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "Introduce yourself."},
        {"role": "user", "content": "are you an AI?"},
        {"role": "assistant", "content": "Lol, fuck off."},
    ]


def test_split_examples_without_examples_keeps_persona():
    assert split_examples("You are Shadow.") == ("You are Shadow.", [])


def test_parse_reply():
    assert parse_reply('{"reply": " Kneel. "}') == "Kneel."


def test_parse_reply_discards_notes():
    content = '{"notes": "Proceed with roleplay, cold tone", "reply": "Kneel."}'
    assert parse_reply(content) == "Kneel."


def test_parse_reply_malformed_is_empty():
    assert parse_reply("Kneel. [Proceed]") == ""
    assert parse_reply('["not", "an object"]') == ""
    assert parse_reply('{"reply": 5}') == ""


def test_describe_message():
    assert describe_message("text", "hi") == "hi"
    assert describe_message("photo", None) == "(sent a photo)"
    assert describe_message("video", "kneeling") == "(sent a video) kneeling"
    assert describe_message("location", None) is None
