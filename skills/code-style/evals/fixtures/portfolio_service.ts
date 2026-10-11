// Portfolio reads for the trading dashboard, on top of a ccxt exchange connection.
import ccxt from "ccxt";

export type PricePoint = { symbol: string; last: number; at: number };

export type PositionValue = { symbol: string; amount: number; valueQuote: number };

export type ServiceConfig = {
  exchangeId: "binance" | "kraken" | "coinbase";
  apiKey: string;
  secret: string;
  quote: string;
};

export class PortfolioService {
  private readonly exchange: ccxt.Exchange;

  constructor(private readonly config: ServiceConfig) {
    const credentials = { apiKey: config.apiKey, secret: config.secret, enableRateLimit: true };
    switch (config.exchangeId) {
      case "binance":
        this.exchange = new ccxt.binance(credentials);
        break;
      case "kraken":
        this.exchange = new ccxt.kraken(credentials);
        break;
      case "coinbase":
        this.exchange = new ccxt.coinbase(credentials);
        break;
    }
  }

  async getPrice(base: string): Promise<PricePoint> {
    const symbol = `${base}/${this.config.quote}`;
    const ticker = await this.exchange.fetchTicker(symbol);
    return { symbol, last: ticker.last ?? 0, at: ticker.timestamp ?? Date.now() };
  }

  async getPrices(bases: string[]): Promise<PricePoint[]> {
    return Promise.all(bases.map((base) => this.getPrice(base)));
  }

  async valuePosition(base: string, amount: number): Promise<PositionValue> {
    const price = await this.getPrice(base);
    return { symbol: price.symbol, amount, valueQuote: amount * price.last };
  }
}
