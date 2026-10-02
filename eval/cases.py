"""Fixed tickets for comparing analysis instructions.

These are inputs only. Expected sentences are not stored here.
"""

EVAL_CASES = [
    {
        "name": "TD-2406",
        "note": "Ambiguous access request. The reading room is the purpose, not the unnamed resource.",
        "repeats": 3,
        "ticket": {
            "id": "TD-2406",
            "subject": "Need access",
            "description": "I need access to the thing from last week. It is urgent for the reading room.",
            "requester": "Samir Adeyemi",
            "department": "Archives",
            "category": "Access",
            "priority": "Medium",
            "status": "New",
            "resolutionNote": "",
            "activity": [
                {
                    "kind": "opened",
                    "body": "Ticket created.",
                    "at": "2026-10-01T09:41:00.000Z",
                }
            ],
        },
    },
    {
        "name": "TD-2404",
        "note": "Clear install request. Program, machine, image, and Friday deadline are already stated.",
        "repeats": 1,
        "ticket": {
            "id": "TD-2404",
            "subject": "Install Larkspur for the cover layout",
            "description": (
                "Please install Larkspur Layout 4 on my design machine, DS-14. "
                "I have a cover due Friday and the trial copy expired. I am on the current Ashmere image."
            ),
            "requester": "Cole Brennan",
            "department": "Design",
            "category": "Software",
            "priority": "Low",
            "status": "New",
            "resolutionNote": "",
            "activity": [
                {
                    "kind": "opened",
                    "body": "Ticket created.",
                    "at": "2026-09-30T10:15:00.000Z",
                }
            ],
        },
    },
    {
        "name": "TD-2403",
        "note": "Activity already records a restart and jobs sitting on production-02. Ticket status is Waiting on User.",
        "repeats": 1,
        "ticket": {
            "id": "TD-2403",
            "subject": "Production printer is ignoring jobs",
            "description": (
                "Jobs sent to the floor printer sit in the queue and never come out. "
                "We are trying to print the galley for the Vale anthology. Other people may be affected. "
                "I tried restarting my computer once."
            ),
            "requester": "Priya Nand",
            "department": "Production",
            "category": "Hardware",
            "priority": "Medium",
            "status": "Waiting on User",
            "resolutionNote": "",
            "activity": [
                {
                    "kind": "opened",
                    "body": "Ticket created.",
                    "at": "2026-09-29T11:04:00.000Z",
                },
                {
                    "kind": "internal",
                    "body": "Print server production-02 shows several jobs sitting in Printing for the floor queue.",
                    "at": "2026-09-29T11:20:00.000Z",
                },
                {
                    "kind": "reply",
                    "body": (
                        "Hello Priya,\n\nI can see jobs stuck in the production queue. "
                        "Which printer name are you choosing, and does the printer panel show a code or a jam?\n\n"
                        "Ashmere Press IT"
                    ),
                    "at": "2026-09-29T11:26:00.000Z",
                },
                {
                    "kind": "status",
                    "body": "Status changed from New to Waiting on User.",
                    "at": "2026-09-29T11:27:00.000Z",
                },
            ],
        },
    },
    {
        "name": "EVAL-ACCESS-2",
        "note": "A different ambiguous access request. The board meeting is the deadline, not the resource.",
        "repeats": 3,
        "ticket": {
            "id": "EVAL-ACCESS-2",
            "subject": "Need access before the board meeting",
            "description": "Can you get me into it before the board meeting? It is urgent.",
            "requester": "Imani Brooks",
            "department": "Membership",
            "category": "Access",
            "priority": "High",
            "status": "New",
            "resolutionNote": "",
            "activity": [
                {
                    "kind": "opened",
                    "body": "Ticket created.",
                    "at": "2026-10-01T16:05:00.000Z",
                }
            ],
        },
    },
]
