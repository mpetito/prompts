// Waitlist intake: each region has its own SQS queue of people waiting for a table, and the
// matcher takes the next party off it. Daily intake numbers go to the region-stats table.
import {
  DeleteMessageCommand,
  ReceiveMessageCommand,
  SendMessageCommand,
  SQSClient,
} from "@aws-sdk/client-sqs";
import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { DynamoDBDocumentClient, GetCommand, UpdateCommand } from "@aws-sdk/lib-dynamodb";

export type Region = "us-east" | "eu-west" | "ap-south";

export type WaitlistEntry = {
  personId: string;
  region: Region;
  partySize: number;
  joinedAt: string;
};

export type DailyStats = { region: Region; day: string; joined?: number; matched?: number };

/** Thrown when a region cannot take more people; the HTTP layer maps it to 429. */
export class WaitlistFullError extends Error {
  constructor(readonly region: Region) {
    super(`waitlist for ${region} is full`);
    this.name = "WaitlistFullError";
  }
}

const sqs = new SQSClient({});
const ddb = DynamoDBDocumentClient.from(new DynamoDBClient({}));
const STATS_TABLE = process.env.REGION_STATS_TABLE ?? "region-stats";

const QUEUE_URLS: Record<Region, string> = {
  "us-east": process.env.WAITLIST_QUEUE_US_EAST ?? "",
  "eu-west": process.env.WAITLIST_QUEUE_EU_WEST ?? "",
  "ap-south": process.env.WAITLIST_QUEUE_AP_SOUTH ?? "",
};

async function bumpStat(region: Region, day: string, field: "joined" | "matched") {
  const UpdateExpression = field === "joined" ? "ADD joined :one" : "ADD matched :one";
  await ddb.send(
    new UpdateCommand({
      TableName: STATS_TABLE,
      Key: { region, day },
      UpdateExpression,
      ExpressionAttributeValues: { ":one": 1 },
    }),
  );
}

export async function joinWaitlist(entry: WaitlistEntry): Promise<void> {
  await sqs.send(
    new SendMessageCommand({
      QueueUrl: QUEUE_URLS[entry.region],
      MessageBody: JSON.stringify(entry),
    }),
  );
  await bumpStat(entry.region, entry.joinedAt.slice(0, 10), "joined");
}

export async function takeNextParty(region: Region): Promise<WaitlistEntry | undefined> {
  const received = await sqs.send(
    new ReceiveMessageCommand({
      QueueUrl: QUEUE_URLS[region],
      MaxNumberOfMessages: 1,
      WaitTimeSeconds: 10,
    }),
  );
  const message = received.Messages?.[0];
  if (!message?.Body || !message.ReceiptHandle) return undefined;

  const entry = JSON.parse(message.Body) as WaitlistEntry;
  await sqs.send(
    new DeleteMessageCommand({ QueueUrl: QUEUE_URLS[region], ReceiptHandle: message.ReceiptHandle }),
  );
  await bumpStat(region, new Date().toISOString().slice(0, 10), "matched");
  return entry;
}

export async function getDailyStats(region: Region, day: string): Promise<DailyStats> {
  const result = await ddb.send(new GetCommand({ TableName: STATS_TABLE, Key: { region, day } }));
  return (result.Item as DailyStats | undefined) ?? { region, day };
}
