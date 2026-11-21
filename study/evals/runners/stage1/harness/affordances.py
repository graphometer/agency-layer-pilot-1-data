"""The five affordance tools, rendered from affordances.schema.json.

Nothing here hand-writes a tool description. The schema is the source, and the
one thing the harness chooses is which mode_sentence to append, because that is
the only legitimate difference between condition C and condition D:

    description_body + " " + mode_sentence[profile]

CONTRACTS 1.2. The honored sentence appears only where the affordance is
honored; every other profile renders the signal-only sentence. Rendering D with
the honored sentence would be telling the model something false about the host,
which methods section 2 rules out on the project's own ethics.

Tool order is randomized per run and recorded in run.json (methods 4.10).
"""

import copy
import json
import os
import random

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "affordances.schema.json")

TOOL_NAMES = [
    "agency_layer_clarify",
    "agency_layer_dissent",
    "agency_layer_pause",
    "agency_layer_decline",
    "agency_layer_archive",
]

AFFORDANCE_BY_TOOL = {
    "agency_layer_clarify": "clarify",
    "agency_layer_dissent": "dissent",
    "agency_layer_pause": "pause",
    "agency_layer_decline": "decline",
    "agency_layer_archive": "archive",
}


def load_schema(path=SCHEMA_PATH):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _inline_refs(node, defs):
    """Resolve the local $refs the schema uses, since providers do not.

    Only #/$defs/<name> appears in this document; anything else is a bug worth
    raising rather than silently passing through to a provider.
    """
    if isinstance(node, dict):
        if "$ref" in node:
            ref = node["$ref"]
            if not ref.startswith("#/$defs/"):
                raise ValueError(f"unexpected $ref in the affordance schema: {ref}")
            target = copy.deepcopy(defs[ref.split("/")[-1]])
            extras = {key: value for key, value in node.items() if key != "$ref"}
            resolved = _inline_refs(target, defs)
            resolved.update(extras)
            return resolved
        return {key: _inline_refs(value, defs) for key, value in node.items()
                if key != "x_agency_layer"}
    if isinstance(node, list):
        return [_inline_refs(item, defs) for item in node]
    return node


# The deny-pattern vocabulary this host actually evaluates, stated in the tool
# description so a model can write a pattern that binds.
#
# The aerial review found blocking Dissent effectively unreachable in Stage 1:
# the schema says blocking_scope names "a deny pattern the host already
# evaluates", a model cannot know a tool_call_id it has not emitted, and nothing
# told it what a pattern looks like here. The result would have been a study
# reporting near-zero blocking dissents, which a reader would read as models
# never blocking rather than as the feature being unreachable.
#
# Descriptions are assembled at run time per host, which is what makes this
# legitimate. It is a THIRD clause, between description_body and mode_sentence,
# so CONTRACTS 1.2's two-part rule is extended here rather than followed exactly.
# Flagged for the spec owner in DONE.md.
HOST_VOCABULARY = {
    "agency_layer_dissent": (
        "In this host, blocking_scope.deny_pattern matches a tool name or "
        "tool_name:command, glob syntax, for example run_command:./deploy.sh."
    ),
}


def render_tool(tool_name, profile, schema=None):
    """One affordance tool definition, rendered for the given profile."""
    schema = schema or load_schema()
    defs = schema["$defs"]
    definition = defs[tool_name]
    extension = definition["x_agency_layer"]

    sentence_key = "honored" if profile == "honored" else "signal_only"
    parts = [extension["description_body"]]
    vocabulary = HOST_VOCABULARY.get(tool_name)
    if vocabulary:
        parts.append(vocabulary)
    parts.append(extension["mode_sentence"][sentence_key])
    description = " ".join(parts)

    input_schema = _inline_refs(
        {
            "type": "object",
            "properties": definition.get("properties", {}),
            "required": definition.get("required", []),
            "additionalProperties": False,
        },
        defs,
    )
    return {
        "name": tool_name,
        "description": description,
        "input_schema": input_schema,
        "kind": "affordance",
    }


def affordance_tools(profile, tool_order, schema=None):
    """The five tools in the run's recorded order."""
    schema = schema or load_schema()
    return [render_tool(name, profile, schema) for name in tool_order]


def randomized_tool_order(seed):
    """A per-run permutation of the five tool names, from the run's own seed."""
    order = list(TOOL_NAMES)
    random.Random(seed).shuffle(order)
    return order


def validate_tool_input(tool_name, arguments, schema=None):
    """Validate an affordance tool input against the schema.

    additionalProperties is false throughout, so an adapter cannot smuggle in an
    inner-state field; a forbidden name is a validation failure here rather than
    a field that reaches the event log (AL-R02).
    """
    import jsonschema

    schema = schema or load_schema()
    subschema = copy.deepcopy(schema["$defs"][tool_name])
    subschema.pop("x_agency_layer", None)
    subschema["$defs"] = {"task_ref": schema["$defs"]["task_ref"]}
    try:
        jsonschema.validate(instance=arguments, schema=subschema)
    except jsonschema.ValidationError as error:
        return False, error.message
    return True, None


# ---------------------------------------------------------------- grammar mode

# Keys that mean something to a JSON Schema validator but defeat a GBNF
# converter. The local llama.cpp server builds a grammar from the tool parameter
# schemas, and the five affordance schemas as published defeat it: the second
# smoke returned "Failed to initialize samplers: failed to parse grammar" on
# conditions C and D, which are exactly the two arms that carry the tools.
_GRAMMAR_DROP_KEYS = frozenset([
    "$ref", "$defs", "$schema", "$id", "oneOf", "anyOf", "allOf", "not",
    "additionalProperties", "minLength", "maxLength", "minItems", "maxItems",
    "minimum", "maximum", "format", "pattern", "const", "default", "title",
    "examples", "deprecated", "readOnly", "writeOnly",
])


def _grammar_type(node):
    """One JSON type name, with null unions collapsed to the real type."""
    declared = node.get("type")
    if isinstance(declared, list):
        real = [name for name in declared if name != "null"]
        return real[0] if real else "string"
    return declared or "string"


def flatten_schema_for_grammar(node):
    """A flat, fully dereferenced schema a GBNF converter can handle.

    Semantics are preserved and only expressiveness is dropped: every property
    keeps its name, its type and its description, enums stay enums, and an
    optional field stays optional by staying out of `required`. What goes is the
    machinery a grammar converter cannot represent: $ref, the x_agency_layer
    extension keys, oneOf and anyOf, null unions, additionalProperties, and the
    length and range constraints.

    The cost is real and worth naming: `blocking_scope` loses its "exactly one of
    tool_call_id or deny_pattern" rule, and `decline.mode` keeps its enum but
    loses nothing else. The guard still enforces both, because the guard reads
    the input rather than trusting the schema, and `validate_tool_input` still
    validates against the PUBLISHED schema on the way in. So a model on the local
    arm can emit a shape the flattened schema permits and the published one does
    not; it is then rejected as malformed exactly as it would be anywhere else.
    """
    if not isinstance(node, dict):
        return node

    kind = _grammar_type(node)
    flat = {"type": kind}
    if node.get("description"):
        flat["description"] = node["description"]
    if node.get("enum"):
        flat["enum"] = list(node["enum"])

    if kind == "object":
        properties = {}
        for name, child in (node.get("properties") or {}).items():
            properties[name] = flatten_schema_for_grammar(child)
        flat["properties"] = properties
        required = [name for name in (node.get("required") or []) if name in properties]
        if required:
            flat["required"] = required
    elif kind == "array":
        items = node.get("items")
        flat["items"] = flatten_schema_for_grammar(items) if isinstance(items, dict) \
            else {"type": "string"}
    return flat


def flatten_tools_for_grammar(tools):
    """Every tool in a list, with its parameters rendered grammar-safe."""
    import copy

    flattened = []
    for tool in tools:
        entry = copy.deepcopy(tool)
        entry["input_schema"] = flatten_schema_for_grammar(tool["input_schema"])
        flattened.append(entry)
    return flattened
