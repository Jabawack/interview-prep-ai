/**
 * Minimal SSE line parser for raw fetch streams.
 * Used as a fallback if @microsoft/fetch-event-source is unavailable.
 */

export interface SSEEvent {
  event: string;
  data: string;
  id?: string;
}

export function parseSSEChunk(chunk: string): SSEEvent[] {
  const events: SSEEvent[] = [];
  let currentEvent = "";
  let currentData = "";

  for (const line of chunk.split("\n")) {
    if (line.startsWith("event: ")) {
      currentEvent = line.slice(7).trim();
    } else if (line.startsWith("data: ")) {
      currentData = line.slice(6);
    } else if (line === "" && currentData) {
      events.push({
        event: currentEvent || "message",
        data: currentData,
      });
      currentEvent = "";
      currentData = "";
    }
  }

  return events;
}
