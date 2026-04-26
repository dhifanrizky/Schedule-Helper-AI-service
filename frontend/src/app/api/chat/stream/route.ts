import { NextRequest } from 'next/server';

type IncomingMessage = {
  role?: string;
  content?: string;
  parts?: Array<{ type?: string; text?: string }>;
};

function normalizeMessageText(message: IncomingMessage) {
  if (typeof message.content === 'string') {
    return message.content;
  }

  if (!Array.isArray(message.parts)) {
    return '';
  }

  return message.parts
    .map((part) => (part?.type === 'text' && typeof part.text === 'string' ? part.text : ''))
    .join('');
}

function buildBackendPayload(body: Record<string, unknown>) {
  const rawMessages = Array.isArray(body.messages) ? (body.messages as IncomingMessage[]) : [];

  const normalizedMessages = rawMessages
    .map((message) => {
      const content = normalizeMessageText(message);
      if (!content) {
        return null;
      }

      return {
        role: message.role === 'user' ? 'user' : 'ai',
        content,
      };
    })
    .filter((message): message is { role: 'user' | 'ai'; content: string } => message !== null);

  const latestUserMessage = [...normalizedMessages].reverse().find((message) => message.role === 'user');

  return {
    user_id: typeof body.user_id === 'string' && body.user_id ? body.user_id : 'anonymous',
    message:
      typeof body.message === 'string' && body.message
        ? body.message
        : latestUserMessage?.content ?? '',
    messages: normalizedMessages,
  };
}

function extractText(data: string) {
  if (!data || data === '[DONE]') {
    return '';
  }

  try {
    const parsed = JSON.parse(data) as Record<string, unknown>;
    const candidate =
      parsed.delta ??
      parsed.text ??
      parsed.content ??
      parsed.message ??
      parsed.output;

    return typeof candidate === 'string' ? candidate : '';
  } catch {
    return data;
  }
}

function parseEventBlock(block: string) {
  let eventName = '';
  const dataLines: string[] = [];

  for (const line of block.split(/\r?\n/)) {
    if (line.startsWith('event:')) {
      eventName = line.slice(6).trim();
      continue;
    }

    if (line.startsWith('data:')) {
      dataLines.push(line.slice(5).trimStart());
    }
  }

  return {
    eventName,
    data: dataLines.join('\n'),
  };
}

export async function POST(req: NextRequest) {
  const body = (await req.json()) as Record<string, unknown>;
  const payload = buildBackendPayload(body);

  // Teruskan ke NestJS
  const response = await fetch('http://localhost:3000/api/agent/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!response.ok || !response.body) {
    return new Response(await response.text(), {
      status: response.status,
      statusText: response.statusText,
      headers: {
        'Content-Type': response.headers.get('content-type') ?? 'text/plain; charset=utf-8',
      },
    });
  }

  const encoder = new TextEncoder();
  const decoder = new TextDecoder();

  const transformedStream = new ReadableStream<Uint8Array>({
    async start(controller) {
      const reader = response.body!.getReader();
      let buffer = '';

      try {
        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            break;
          }

          buffer += decoder.decode(value, { stream: true });

          const blocks = buffer.split(/\r?\n\r?\n/);
          buffer = blocks.pop() ?? '';

          for (const block of blocks) {
            const { eventName, data } = parseEventBlock(block);

            if (eventName === 'execution_complete') {
              continue;
            }

            const text = extractText(data);
            if (text) {
              controller.enqueue(encoder.encode(text));
            }
          }
        }

        const finalChunk = buffer + decoder.decode();
        if (finalChunk.trim()) {
          const { eventName, data } = parseEventBlock(finalChunk);
          if (eventName !== 'execution_complete') {
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

  // Kembalikan sebagai plain text stream agar kompatibel dengan TextStreamChatTransport.
  return new Response(transformedStream, {
    status: response.status,
    statusText: response.statusText,
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
      'Cache-Control': 'no-cache',
    },
  });
}