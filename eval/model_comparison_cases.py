"""The ten seeded TinyDesk tickets, with full activity and resolution notes.

Timestamps match js/store.js: Date.UTC(2026, month - 1, day, hour, minute).
"""

from datetime import datetime, timezone


def at(month: int, day: int, hour: int, minute: int) -> str:
    stamp = datetime(2026, month, day, hour, minute, tzinfo=timezone.utc)
    return stamp.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def act(kind: str, body: str, month: int, day: int, hour: int, minute: int) -> dict:
    return {"kind": kind, "body": body, "at": at(month, day, hour, minute)}


def ticket(fields: dict) -> dict:
    activity = fields["activity"]
    payload = {
        "resolutionNote": "",
        **fields,
    }
    payload["activity"] = activity
    return payload


SEEDED_TICKETS = [
    ticket({
        "id": "TD-2401",
        "subject": "Home VPN will not connect",
        "requester": "Mara Ellison",
        "department": "Editorial",
        "category": "Network",
        "priority": "High",
        "status": "In Progress",
        "description": (
            'I am working from home today and the Ashmere VPN client stops at "contacting gateway." '
            "It worked on Thursday from the office. I need the style guide share before the afternoon proof."
        ),
        "activity": [
            act("opened", "Ticket created.", 9, 28, 14, 12),
            act("status", "Status changed from New to In Progress.", 9, 28, 14, 40),
            act(
                "internal",
                "Checked the Ashmere VPN profile on Mara's laptop record. The client is installed. Still need the error text from the home connection.",
                9, 28, 15, 5,
            ),
            act(
                "internal",
                "Mara pinged again before the afternoon proof. Still blocked at contacting gateway.",
                10, 1, 9, 20,
            ),
        ],
    }),
    ticket({
        "id": "TD-2402",
        "subject": "Password reset",
        "requester": "Jonah Peck",
        "department": "Finance",
        "category": "Other",
        "priority": "Medium",
        "status": "New",
        "description": "Can't get in. Please reset.",
        "activity": [act("opened", "Ticket created.", 10, 1, 8, 22)],
    }),
    ticket({
        "id": "TD-2403",
        "subject": "Production printer is ignoring jobs",
        "requester": "Priya Nand",
        "department": "Production",
        "category": "Hardware",
        "priority": "Medium",
        "status": "Waiting on User",
        "description": (
            "Jobs sent to the floor printer sit in the queue and never come out. "
            "We are trying to print the galley for the Vale anthology. Other people may be affected. "
            "I tried restarting my computer once."
        ),
        "activity": [
            act("opened", "Ticket created.", 9, 29, 11, 4),
            act(
                "internal",
                "Print server production-02 shows several jobs sitting in Printing for the floor queue.",
                9, 29, 11, 20,
            ),
            act(
                "reply",
                "Hello Priya,\n\nI can see jobs stuck in the production queue. Which printer name are you choosing, and does the printer panel show a code or a jam?\n\nAshmere Press IT",
                9, 29, 11, 26,
            ),
            act("status", "Status changed from New to Waiting on User.", 9, 29, 11, 27),
        ],
    }),
    ticket({
        "id": "TD-2404",
        "subject": "Install Larkspur for the cover layout",
        "requester": "Cole Brennan",
        "department": "Design",
        "category": "Software",
        "priority": "Low",
        "status": "New",
        "description": (
            "Please install Larkspur Layout 4 on my design machine, DS-14. "
            "I have a cover due Friday and the trial copy expired. I am on the current Ashmere image."
        ),
        "activity": [act("opened", "Ticket created.", 9, 30, 10, 15)],
    }),
    ticket({
        "id": "TD-2405",
        "subject": "Mail from outside Ashmere is not arriving",
        "requester": "Elise Voss",
        "department": "Communications",
        "category": "Email",
        "priority": "High",
        "status": "In Progress",
        "description": (
            "Since Monday I have not received messages from authors. Internal mail still works. "
            "I checked the junk folder. One author said their message did not bounce. It just never showed up."
        ),
        "activity": [
            act("opened", "Ticket created.", 9, 27, 9, 12),
            act("status", "Status changed from New to In Progress.", 9, 27, 9, 40),
            act(
                "internal",
                "Gateway log shows accepted connections from inside Ashmere and no recent mail from the outside domains on the communications list. No bounce is generated when a message is dropped at the spam threshold.",
                10, 1, 7, 48,
            ),
        ],
    }),
    ticket({
        "id": "TD-2406",
        "subject": "Need access",
        "requester": "Samir Adeyemi",
        "department": "Archives",
        "category": "Access",
        "priority": "Medium",
        "status": "New",
        "description": "I need access to the thing from last week. It is urgent for the reading room.",
        "activity": [act("opened", "Ticket created.", 10, 1, 9, 41)],
    }),
    ticket({
        "id": "TD-2407",
        "subject": "VPN drops every few minutes",
        "requester": "Ruth Calder",
        "department": "Field Desk",
        "category": "Network",
        "priority": "Medium",
        "status": "New",
        "description": (
            "When I am on a site visit the VPN connects, then disconnects after about ten minutes. "
            "I was on a public library wifi today. Reconnecting works until it drops again. "
            "Chat stays open, but the archive share disappears."
        ),
        "activity": [act("opened", "Ticket created.", 9, 30, 15, 8)],
    }),
    ticket({
        "id": "TD-2408",
        "subject": "Sticky keys on loaner laptop LP-14",
        "requester": "Theo Lang",
        "department": "Facilities",
        "category": "Hardware",
        "priority": "Low",
        "status": "Resolved",
        "resolutionNote": "Replaced the keyboard on loaner LP-14 and confirmed typing in the facilities log.",
        "description": (
            "The loaner laptop for the loading dock repeats letters. "
            "I turned off the accessibility sticky keys setting and it still happens. Mostly the E and O keys."
        ),
        "activity": [
            act("opened", "Ticket created.", 9, 24, 13, 22),
            act("status", "Status changed from New to In Progress.", 9, 24, 13, 40),
            act(
                "internal",
                "Accessibility sticky keys was already off. The E and O keys repeat when the dock loaner is tilted, so this looks like the keyboard, not the setting.",
                9, 25, 10, 50,
            ),
            act(
                "status",
                "Status changed from In Progress to Resolved. Resolution: Replaced the keyboard on loaner LP-14 and confirmed typing in the facilities log.",
                9, 25, 11, 5,
            ),
        ],
    }),
    ticket({
        "id": "TD-2409",
        "subject": "Notes to partner groups are bouncing",
        "requester": "Nina Okonkwo",
        "department": "Membership",
        "category": "Email",
        "priority": "Medium",
        "status": "Waiting on User",
        "description": (
            "Messages to our partner reading groups come back as undeliverable. "
            "It started after I changed my signature. Internal messages go through. "
            "I can forward a sample if you tell me where."
        ),
        "activity": [
            act("opened", "Ticket created.", 9, 26, 8, 33),
            act(
                "reply",
                "Hello Nina,\n\nInternal mail working while partner mail bounces usually points at the recipient address or a signature file, not the whole mailbox.\n\nPlease forward one full bounce, including the address you typed and any error code.\n\nAshmere Press IT",
                9, 26, 9, 10,
            ),
            act("status", "Status changed from New to Waiting on User.", 9, 26, 9, 11),
        ],
    }),
    ticket({
        "id": "TD-2410",
        "subject": "Program will not open",
        "requester": "Wren Hale",
        "department": "Research",
        "category": "Software",
        "priority": "High",
        "status": "In Progress",
        "description": "The program will not open and I have a deadline tonight. It just flashes and closes. Please fix it.",
        "activity": [
            act("opened", "Ticket created.", 10, 1, 6, 58),
            act("status", "Status changed from New to In Progress.", 10, 1, 8, 2),
            act(
                "internal",
                "Subject does not name the program. Pausing until Wren sends the application name and whether a window or an error flashes.",
                10, 1, 8, 6,
            ),
        ],
    }),
]

REPEATS = {"TD-2406": 3, "TD-2408": 3}
