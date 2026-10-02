/**
 * Ask the TinyDesk server to analyze one saved ticket.
 * The result shape is:
 *   { available: true, summary, suggestedCategory, followUps, draft }
 *   { available: false, message, retry }
 */

function unavailable(message, retry) {
  return { available: false, message, retry: Boolean(retry) };
}

function isAnalysis(body) {
  return Boolean(
    body &&
      body.available === true &&
      typeof body.summary === "string" &&
      typeof body.suggestedCategory === "string" &&
      typeof body.draft === "string" &&
      Array.isArray(body.followUps) &&
      body.followUps.every((item) => typeof item === "string")
  );
}

export async function analyzeTicket(ticket, options) {
  const signal = options && options.signal;
  if (!ticket || typeof ticket !== "object" || !ticket.id) {
    return unavailable("Open a ticket before asking for a suggestion.", false);
  }

  const activity = Array.isArray(ticket.activity) ? ticket.activity : [];
  const payload = {
    id: ticket.id,
    subject: ticket.subject || "",
    description: ticket.description || "",
    requester: ticket.requester || "",
    department: ticket.department || "",
    category: ticket.category || "",
    priority: ticket.priority || "",
    status: ticket.status || "",
    resolutionNote: ticket.resolutionNote || "",
    activity: activity.map((item) => ({
      kind: item && item.kind ? String(item.kind) : "",
      body: item && item.body ? String(item.body) : "",
      at: item && item.at ? String(item.at) : ""
    }))
  };

  let response;
  try {
    response = await fetch("/api/analyze-ticket", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json"
      },
      body: JSON.stringify(payload),
      signal
    });
  } catch (error) {
    if (error && error.name === "AbortError") throw error;
    return unavailable(
      "TinyDesk could not reach the analysis service. Check that the TinyDesk server is running, then try again.",
      true
    );
  }

  let body = null;
  try {
    body = await response.json();
  } catch {
    body = null;
  }

  if (body && body.available === false && typeof body.message === "string" && body.message.trim()) {
    return unavailable(body.message, true);
  }
  if (!response.ok || !isAnalysis(body)) {
    return unavailable("Analysis could not be completed. Try again.", true);
  }

  return {
    available: true,
    summary: body.summary,
    suggestedCategory: body.suggestedCategory,
    followUps: body.followUps.slice(),
    draft: body.draft
  };
}
