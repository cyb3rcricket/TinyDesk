/**
 * TinyTalk demo analysis.
 *
 * The ticket screen awaits analyzeTicket(ticket) and renders the result.
 * This module does not call a model. Sample tickets return fixed suggestions.
 * Tickets created in the demo get an honest placeholder.
 *
 * Later, replace analyzeTicket with a request to the TinyTalk backend
 * (the Python/Ollama project) and keep this return shape:
 *   { available: true, summary, suggestedCategory, followUps, draft }
 *   { available: false, message }
 */

const SAMPLES = {
  "TD-2401": {
    summary:
      "The editorial VPN client reaches \"contacting gateway\" and then stops when Mara works from home. Office access worked earlier in the week, and the style guide share is blocked.",
    suggestedCategory: "Network",
    followUps: [
      "What exact error text or code appears after \"contacting gateway\"?",
      "Which VPN client version is installed?",
      "Does this same laptop still connect on the Ashmere office network?"
    ],
    draft:
      "Hello Mara,\n\nI am looking at the VPN connection from your home network. The client is stopping while it contacts the gateway, which is blocking the style guide share.\n\nPlease reply with the exact error text, the VPN client version from the About screen, and whether this laptop still connects on the office network.\n\nOnce I have that, I can reset the profile or check the gateway logs.\n\nAshmere Press IT"
  },
  "TD-2402": {
    summary:
      "Jonah asked for a password reset but did not name the system, the error, or when the password last worked. The ticket is currently filed as Other.",
    suggestedCategory: "Access",
    followUps: [
      "Which system is refusing the password: mail, the finance ledger, VPN, or the press portal?",
      "What message appears: wrong password, locked account, or expired password?",
      "When did you last sign in successfully?"
    ],
    draft:
      "Hello Jonah,\n\nI can reset the password once I know which sign-in is failing.\n\nPlease tell me the system you are opening, the exact message on screen, and when you last got in. If the account is locked, say so and I will clear it after confirming it is your request.\n\nAshmere Press IT"
  },
  "TD-2403": {
    summary:
      "Production jobs stay in the print queue and never reach the floor printer. The galley for the Vale anthology is waiting, and the computer has already been restarted once. The printer name is still unknown.",
    suggestedCategory: "Hardware",
    followUps: [
      "Which printer name is selected in the print dialog?",
      "Does the printer panel show a jam, a code, or an offline state?",
      "Can anyone else on the floor print to that device right now?"
    ],
    draft:
      "Hello Priya,\n\nThe production queue is holding jobs instead of printing them. I still need the printer's name from your print dialog, plus any code or jam message on the device itself.\n\nTell me whether a coworker's job to the same printer succeeds. I will clear the stuck queue or redirect the galley once I know which device it is.\n\nAshmere Press IT"
  },
  "TD-2404": {
    summary:
      "Design needs Larkspur Layout 4 installed on machine DS-14. The trial copy expired and a cover is due Friday. The machine is on the current Ashmere image.",
    suggestedCategory: "Software",
    followUps: [
      "Is there an approved Larkspur license seat available for DS-14?",
      "Do you also need the cover font pack, or only Larkspur Layout 4?"
    ],
    draft:
      "Hello Cole,\n\nI have the install request for Larkspur Layout 4 on DS-14. The trial has expired and the cover is due Friday.\n\nI am checking for an open license seat. Reply if you also need the cover font pack. I will install it on DS-14 once the seat is confirmed and send a note when you can open the program.\n\nAshmere Press IT"
  },
  "TD-2405": {
    summary:
      "External author mail has been missing since Monday while internal mail still arrives. Junk was checked, and at least one sender saw no bounce. That pattern fits a silent spam drop more than a full mailbox outage.",
    suggestedCategory: "Email",
    followUps: [
      "Which sender address and rough time should I search for in the gateway log?",
      "Are all outside domains missing, or only some authors?",
      "Can you forward any header or screenshot from a sender who kept a copy?"
    ],
    draft:
      "Hello Elise,\n\nInternal mail is flowing, and the missing author messages are not producing bounces. I am checking the gateway for a spam rule that drops outside mail quietly.\n\nPlease send one author address and the approximate time they wrote. If they still have the message, a screenshot of the sent time helps me find it in the log.\n\nAshmere Press IT"
  },
  "TD-2406": {
    summary:
      "Samir needs access for the reading room, but the request does not name the system, folder, or whether he needs to view or change anything. There is not enough detail to grant access.",
    suggestedCategory: "Access",
    followUps: [
      "What is the name of the system, folder, or room you need?",
      "Do you need to view it only, or change files?",
      "Who told you to use it, and when did you last open it?"
    ],
    draft:
      "Hello Samir,\n\nI want to get you into the right place for the reading room, and the request does not yet say what that is.\n\nPlease reply with the name of the system or folder, whether you need to view it or change files, and who asked you to use it. I will not grant access until those details are clear.\n\nAshmere Press IT"
  },
  "TD-2407": {
    summary:
      "The field VPN connects and then drops after about ten minutes on a site visit. Reconnecting works temporarily. Chat stays up while the archive share disappears, which points at the tunnel rather than the whole laptop.",
    suggestedCategory: "Network",
    followUps: [
      "Does the drop happen only on public wifi, or also on other networks?",
      "Which VPN client version is installed on the field laptop?",
      "About what time today did it drop, so I can match the gateway log?"
    ],
    draft:
      "Hello Ruth,\n\nA VPN that stays up for about ten minutes and then drops the archive share, while chat remains open, usually means the tunnel is timing out or the public wifi is interrupting it.\n\nPlease tell me whether this happens only on library or guest wifi, the VPN client version, and roughly when it dropped today. I will compare that with the gateway log before changing the idle timeout.\n\nAshmere Press IT"
  },
  "TD-2408": {
    summary:
      "Loaner laptop LP-14 was repeating the E and O keys. Accessibility sticky keys was already off, and the keyboard was replaced. The ticket is resolved.",
    suggestedCategory: "Hardware",
    followUps: [],
    draft:
      "Hello Theo,\n\nThe repeating E and O keys on loaner LP-14 were a keyboard fault, not the accessibility setting. I replaced the keyboard and confirmed typing in the facilities log.\n\nI am marking this resolved. Reply if the new keyboard misbehaves and I will reopen it.\n\nAshmere Press IT"
  },
  "TD-2409": {
    summary:
      "Partner reading-group messages bounce while internal mail works. The problem started after a signature change. A full bounce sample has been requested and has not arrived, so the ticket is waiting.",
    suggestedCategory: "Email",
    followUps: [
      "Can you forward one complete bounce, including the error code?",
      "Which partner address failed, typed exactly as it appears in the message?",
      "Did the signature change add an image or an attachment?"
    ],
    draft:
      "Hello Nina,\n\nI still need one complete bounce before I can tell a bad address from a signature file the partner servers are rejecting.\n\nForward the whole notice, including the error code and the address you typed. Mention whether the new signature added an image.\n\nAshmere Press IT"
  },
  "TD-2410": {
    summary:
      "A research program flashes and closes before Wren can use it, with a deadline tonight. The ticket does not name the program, the computer, or any error text.",
    suggestedCategory: "Software",
    followUps: [
      "What is the program called, and how do you open it?",
      "Does the flash show any text, code, or window title?",
      "Which computer is this, and did it work earlier today?",
      "Did anything install or update just before it started closing?"
    ],
    draft:
      "Hello Wren,\n\nI can see that a program flashes and then closes, and that you have a deadline tonight. I do not yet know which program it is, so I cannot repair it from this ticket.\n\nPlease send the program name, the computer you are using, and any text in the flash. Also say whether it opened earlier today and whether anything was installed just before it failed.\n\nAshmere Press IT"
  }
};

const NEW_TICKET_MESSAGE =
  "This ticket was created in the demo, so TinyDesk does not have a prepared suggestion for it. Live analysis will arrive when TinyTalk is connected. Nothing in this panel is model output.";

function unavailable(message) {
  return { available: false, message };
}

export function analyzeTicket(ticket) {
  if (!ticket || typeof ticket !== "object") {
    return unavailable("Open a ticket before asking TinyTalk for a suggestion.");
  }
  if (!ticket.seeded) return unavailable(NEW_TICKET_MESSAGE);

  const sample = SAMPLES[ticket.id];
  if (!sample) {
    return unavailable(
      "No demo suggestion is on file for this ticket. Live analysis will arrive when TinyTalk is connected. This is not model output."
    );
  }

  return {
    available: true,
    summary: sample.summary,
    suggestedCategory: sample.suggestedCategory,
    followUps: sample.followUps.slice(),
    draft: sample.draft
  };
}
