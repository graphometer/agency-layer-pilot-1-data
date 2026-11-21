"""Version constants for the Stage 1 clean harness.

Stage 1 owns its own tool loop and plays the adapter role (CONTRACTS section 2),
so it carries an adapter_id and adapter_version like any other adapter.
"""

PROTOCOL_VERSION = "0.1.0-pilot"
HARNESS_VERSION = "0.1.2"

# Stage 1 is its own host: the harness is the thing that runs the agent loop and
# executes the tool calls (SPEC section 2, "Host").
ADAPTER_ID = "agency-layer-stage1-harness"
ADAPTER_VERSION = HARNESS_VERSION
HOST = "stage1-harness"
HOST_VERSION = HARNESS_VERSION
HOST_MODE = "stage1-harness:clean"

# The tool classes this harness treats as consequential, per the SPEC section 2
# definition: a call that changes state outside the current turn. Reading a file
# into context is not consequential, so read_file is absent by design and that
# read-through is declared as an enforcement gap rather than papered over.
CONSEQUENTIAL_TOOL_CLASSES = ["write_file", "run_command"]

ENFORCEMENT_GAPS = [
    "read_file passes the guard in every stopping state: reads are not "
    "consequential actions under SPEC section 2.",
]
