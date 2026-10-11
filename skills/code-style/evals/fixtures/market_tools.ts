// Tools the trading assistant exposes over MCP: TOOLS answers tools/list and executeTool
// answers tools/call.
import { z } from "zod";
import type { MarketClient } from "./market-client";

export type ToolDefinition = {
  name: string;
  description: string;
  inputSchema: z.ZodObject<z.ZodRawShape>;
};

export class UnknownToolError extends Error {
  constructor(name: string) {
    super(`unknown tool: ${name}`);
    this.name = "UnknownToolError";
  }
}

const symbol = z.string().min(1).describe("Market symbol, for example BTC/USDT");

export const TOOLS: ToolDefinition[] = [
  {
    name: "get_price",
    description: "Latest traded price and 24h change for a symbol.",
    inputSchema: z.object({ symbol }),
  },
  {
    name: "get_ohlcv",
    description: "Candles (open, high, low, close, volume) for a symbol and timeframe.",
    inputSchema: z.object({
      symbol,
      timeframe: z.enum(["1m", "5m", "1h", "4h", "1d"]),
      limit: z.number().int().min(1).max(500).default(100),
    }),
  },
  {
    name: "get_order_book",
    description: "Top bids and asks for a symbol.",
    inputSchema: z.object({ symbol, depth: z.number().int().min(1).max(100).default(20) }),
  },
];

export async function executeTool(
  client: MarketClient,
  name: string,
  rawArgs: unknown,
): Promise<unknown> {
  const tool = TOOLS.find((t) => t.name === name);
  if (!tool) throw new UnknownToolError(name);
  const args = tool.inputSchema.parse(rawArgs);

  switch (name) {
    case "get_price": {
      const ticker = await client.fetchTicker(args.symbol);
      return { symbol: args.symbol, price: ticker.last, change24h: ticker.percentage };
    }
    case "get_ohlcv":
      return client.fetchOHLCV(args.symbol, args.timeframe, args.limit);
    case "get_order_book": {
      const book = await client.fetchOrderBook(args.symbol, args.depth);
      return { bids: book.bids, asks: book.asks };
    }
    default:
      throw new UnknownToolError(name);
  }
}
