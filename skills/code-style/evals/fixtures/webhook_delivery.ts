import { createHmac } from "node:crypto";

export type WebhookEndpoint = { url: string; secret: string };

export type WebhookEvent = { id: string; type: string; createdAt: string; data: unknown };

export type DeliveryResult =
  | { ok: true; status: number }
  | { ok: false; status?: number; error: string };

function sign(secret: string, timestamp: string, body: string): string {
  return createHmac("sha256", secret).update(`${timestamp}.${body}`).digest("hex");
}

export async function deliverWebhook(
  endpoint: WebhookEndpoint,
  event: WebhookEvent,
  fetchImpl: typeof fetch = fetch,
): Promise<DeliveryResult> {
  const body = JSON.stringify(event);
  const timestamp = Math.floor(Date.now() / 1000).toString();
  try {
    const res = await fetchImpl(endpoint.url, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "webhook-id": event.id,
        "webhook-timestamp": timestamp,
        "webhook-signature": `v1=${sign(endpoint.secret, timestamp, body)}`,
      },
      body,
    });
    return res.ok ? { ok: true, status: res.status } : { ok: false, status: res.status, error: `HTTP ${res.status}` };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) };
  }
}
