import { NextRequest } from "next/server";
type IncomingMessage = {
  role?: string;
  content?: string;
  parts?: Array<{ type?: string; text?: string }>;
};

function normalizeMessageText(message: IncomingMessage) {
  if (typeof message.content === "string") return message.content;
  if (!Array.isArray(message.parts)) return "";
  return message.parts
    .map((part) =>
      part?.type === "text" && typeof part.text === "string" ? part.text : "",
    )
    .join("");
}

type ResumePayload = {
  user_id: string;
  thread_id: string;
  approved_data:
    | { approved: boolean; edited_draft: string | null } // Counselor
    | { tasks: { task: string; priority: number; deadline: string }[] }; // Prioritizer
};

type ChatPayload = {
  user_id: string;
  message: string;
  messages: { role: "user" | "system"; content: string }[];
  thread_id?: string;
};

function buildBackendPayload(
  body: Record<string, unknown>,
): ChatPayload | ResumePayload {
  const userId =
    typeof body.user_id === "string" && body.user_id
      ? body.user_id
      : "anonymous";

  // ✅ Deteksi resume: ada approved_data dan thread_id
  if (
    body.approved_data !== undefined &&
    typeof body.thread_id === "string" &&
    body.thread_id
  ) {
    return {
      user_id: userId,
      thread_id: body.thread_id,
      approved_data: body.approved_data as ResumePayload["approved_data"],
    };
  }

  // Normal chat payload
  const rawMessages = Array.isArray(body.messages)
    ? (body.messages as IncomingMessage[])
    : [];

  const normalizedMessages = rawMessages
    .map((message) => {
      const content = normalizeMessageText(message);
      if (!content) return null;
      return {
        role: message.role === "user" ? "user" : "system",
        content,
      };
    })
    .filter(
      (m): m is { role: "user" | "system"; content: string } => m !== null,
    );

  const latestUserMessage = [...normalizedMessages]
    .reverse()
    .find((m) => m.role === "user");

  return {
    user_id: userId,
    message:
      typeof body.message === "string" && body.message
        ? body.message
        : (latestUserMessage?.content ?? ""),
    ...(typeof body.thread_id === "string" && body.thread_id
      ? { thread_id: body.thread_id }
      : {}),
    messages: normalizedMessages,
  };
}

function extractText(data: string): string {
  if (!data || data === "[DONE]") return "";
  try {
    const parsed = JSON.parse(data) as Record<string, unknown>;
    const candidate =
      parsed.delta ??
      parsed.text ??
      parsed.content ??
      parsed.message ??
      parsed.output;
    return typeof candidate === "string" ? candidate : "";
  } catch {
    return "";
  }
}

/**
 * Extract thread_id dari data SSE event agent_step.
 * Format: { "thread_id": "...", "update": { ... } }
 */
function extractThreadId(data: string): string | null {
  try {
    const parsed = JSON.parse(data) as Record<string, unknown>;
    if (typeof parsed.thread_id === "string" && parsed.thread_id) {
      return parsed.thread_id;
    }
    return null;
  } catch {
    return null;
  }
}

function parseEventBlock(block: string) {
  let eventName = "";
  const dataLines: string[] = [];

  for (const line of block.split(/\r?\n/)) {
    if (line.startsWith("event:")) {
      eventName = line.slice(6).trim();
      continue;
    }
    if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trimStart());
    }
  }

  return { eventName, data: dataLines.join("\n") };
}

export async function POST(req: NextRequest) {
  const body = (await req.json()) as Record<string, unknown>;
  const payload = buildBackendPayload(body);

  const authHeader = req.headers.get("Authorization");
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (authHeader) {
    headers["Authorization"] = authHeader;
  }

  const response = await fetch(process.env.NEXT_PUBLIC_API_URL ? `${process.env.NEXT_PUBLIC_API_URL}/agent/stream` : "http://localhost:3000/api/agent/stream", {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
  });

  if (!response.ok || !response.body) {
    return new Response(await response.text(), {
      status: response.status,
      statusText: response.statusText,
      headers: {
        "Content-Type":
          response.headers.get("content-type") ?? "text/plain; charset=utf-8",
      },
    });
  }

  const encoder = new TextEncoder();
  const decoder = new TextDecoder();

  let threadIdEmitted = false;

  const transformedStream = new ReadableStream<Uint8Array>({
    async start(controller) {
      const reader = response.body!.getReader();
      let buffer = "";

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const blocks = buffer.split(/\r?\n\r?\n/);
          buffer = blocks.pop() ?? "";

          for (const block of blocks) {
            const { eventName, data } = parseEventBlock(block);

            if (eventName === "execution_complete") {
              controller.enqueue(
                encoder.encode(`\x00EXECUTION_COMPLETE:${data}\x00`),
              );
              continue;
            }

            // ✅ Emit thread_id sekali sebagai token khusus di awal stream
            if (!threadIdEmitted) {
              const threadId = extractThreadId(data);
              if (threadId) {
                // Kirim sebagai token khusus yang akan diparsing oleh useChat
                // Format: \x00THREAD_ID:<id>\x00 (non-printable prefix agar tidak tampil ke user)
                controller.enqueue(
                  encoder.encode(`\x00THREAD_ID:${threadId}\x00`),
                );
                threadIdEmitted = true;
              }
            }

            const text = extractText(data);
            if (text) {
              controller.enqueue(encoder.encode(text));
            }
          }
        }

        // Proses sisa buffer
        const finalChunk = buffer + decoder.decode();
        if (finalChunk.trim()) {
          const { eventName, data } = parseEventBlock(finalChunk);

          if (eventName === "execution_complete") {
            controller.enqueue(
              encoder.encode(`\x00EXECUTION_COMPLETE:${data}\x00`),
            );
          } else {
            if (!threadIdEmitted) {
              const threadId = extractThreadId(data);
              if (threadId) {
                controller.enqueue(
                  encoder.encode(`\x00THREAD_ID:${threadId}\x00`),
                );
                threadIdEmitted = true;
              }
            }
            const text = extractText(data);
            if (text) {
              controller.enqueue(encoder.encode(text));
            }
          }
        }

        controller.close();
      } catch (error) {
        controller.error(error);
      } finally {
        reader.releaseLock();
      }
    },
  });

  return new Response(transformedStream, {
    status: response.status,
    statusText: response.statusText,
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": "no-cache",
    },
  });
}
