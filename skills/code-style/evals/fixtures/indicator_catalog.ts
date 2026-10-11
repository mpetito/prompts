// Technical indicators the chart service and the price-alert service can compute, by name.
export type Candle = { time: number; open: number; high: number; low: number; close: number; volume: number };

export type IndicatorSpec = {
  name: string;
  label: string;
  overlay: boolean;
  params: Record<string, number>;
  compute: (candles: Candle[], params: Record<string, number>) => number[];
};

export function defineIndicator(spec: IndicatorSpec): IndicatorSpec {
  return spec;
}

/** Builds a spec from a close-price function with a single `period` parameter. */
export function createSpec(
  name: string,
  label: string,
  period: number,
  compute: (closes: number[], period: number) => number[],
): IndicatorSpec {
  return {
    name,
    label,
    overlay: false,
    params: { period },
    compute: (candles, params) => compute(candles.map((c) => c.close), params.period),
  };
}

const sma = defineIndicator({
  name: "sma",
  label: "Simple moving average",
  overlay: true,
  params: { period: 20 },
  compute: (candles, { period }) =>
    candles.map((_, i) => {
      if (i + 1 < period) return NaN;
      const window = candles.slice(i + 1 - period, i + 1);
      return window.reduce((sum, c) => sum + c.close, 0) / period;
    }),
});

const ema = defineIndicator({
  name: "ema",
  label: "Exponential moving average",
  overlay: true,
  params: { period: 20 },
  compute: (candles, { period }) => {
    const k = 2 / (period + 1);
    const out: number[] = [];
    candles.forEach((c, i) => out.push(i === 0 ? c.close : c.close * k + out[i - 1] * (1 - k)));
    return out;
  },
});

const vwap = defineIndicator({
  name: "vwap",
  label: "Volume-weighted average price",
  overlay: true,
  params: {},
  compute: (candles) => {
    let pv = 0;
    let volume = 0;
    return candles.map((c) => {
      pv += ((c.high + c.low + c.close) / 3) * c.volume;
      volume += c.volume;
      return volume === 0 ? NaN : pv / volume;
    });
  },
});

const rsi = createSpec("rsi", "Relative strength index", 14, (closes, period) => {
  let gain = 0;
  let loss = 0;
  return closes.map((close, i) => {
    if (i === 0) return NaN;
    const change = close - closes[i - 1];
    gain = (gain * (period - 1) + Math.max(change, 0)) / period;
    loss = (loss * (period - 1) + Math.max(-change, 0)) / period;
    if (i < period) return NaN;
    return loss === 0 ? 100 : 100 - 100 / (1 + gain / loss);
  });
});

const roc = createSpec("roc", "Rate of change", 10, (closes, period) =>
  closes.map((close, i) => (i < period ? NaN : ((close - closes[i - period]) / closes[i - period]) * 100)),
);

export const INDICATORS: Record<string, IndicatorSpec> = Object.fromEntries(
  [sma, ema, vwap, rsi, roc].map((spec) => [spec.name, spec]),
);
