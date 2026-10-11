// Builds the home dashboard's cards from the tools on our MCP server (packages/mcp-server).
import { mcp } from "./mcp-client";

export type PriceRow = { symbol: string; price: number; change24h: number };
export type NewsItem = { id: string; title: string; url: string; publishedAt: string };
export type WatchlistRow = { symbol: string; note?: string };

export type Dashboard = {
  prices: PriceRow[];
  news: NewsItem[];
  watchlist: WatchlistRow[];
};

async function callTool<T>(name: string, args: Record<string, unknown>): Promise<T> {
  const result = await mcp.callTool({ name, arguments: args });
  if (result.isError) {
    throw new Error(`${name} failed: ${JSON.stringify(result.content)}`);
  }
  return result.structuredContent as T;
}

export async function loadDashboard(userId: string, symbols: string[]): Promise<Dashboard> {
  const [prices, news, watchlist] = await Promise.all([
    callTool<PriceRow[]>("get_prices", { symbols }),
    callTool<NewsItem[]>("get_news", { symbols, limit: 8 }),
    callTool<WatchlistRow[]>("get_watchlist", { userId }),
  ]);
  return { prices, news, watchlist };
}
