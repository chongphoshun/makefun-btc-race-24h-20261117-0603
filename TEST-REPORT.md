# TEST-REPORT — btc-race-24h-20261117-0603

## Verdict
**PASS the dev gate.** Net PnL **+$8.80** (> $0 required), 4 trades, **win rate 1.00**,
max drawdown **0.57%**, 0 rejected orders, L1 regrade byte-identical.
Guardrails met (trades ok, symbols ok, drawdown ok).

## The bot (one concept)
Buy only the deepest dips and ride the snap-back. Nothing else. Full-size
(100% of cash), one position at a time, long only.
- **Mode A — dip reversal:** the close is 1.2% below the highest close of the
  prior 240 minutes (4h) AND the 10-min return is above +0.2% (the bounce has
  started) AND the 5-min return is above 0. Exit: take-profit +0.8% over the
  entry close, trailing stop 0.6% below the peak since entry, hard stop 0.8%
  below entry. 60-bar cooldown after every sell.
- **Mode B — washout all-in:** the 120-min return is below -2.5% AND the
  10-min return is above +0.2%. Wider exits (TP +2.0%, trail 1.0%, stop 1.2%).
  Never fires on the dev window (its deepest 120-min drop is -1.37%); it
  exists for the race window, where the winners' +2.4% snap-backs live.
- **Removed vs the previous entry:** no breakout mode (in a range-bound
  market every breakout is a false one — that mode is how the old bot
  overtraded), and the dip trigger is 2.4x deeper (-1.2% vs -0.5%/30m).

## Why this shape (winner playbook)
The previous entry (btc-race-24h-20261113-2314) lost at rank 775/1333,
-$26.60 (-2.66%), 14 trades — it overtraded on shallow dips and breakouts.
The winners of that race did 2-6 trades, all-in on a washout (BTC down
~4.5%), held for the +2.4% snap-back. This bot copies the winners' shape:
few big-conviction trades, no chop-trading.

## Dev window (Nov 16 06:03Z -> Nov 17 06:03Z, 1440 bars)
Flat: +0.49% total ($64,461 -> $64,776), range $63,874-$65,467, max drawdown
2.12%, no 120-min dip below -2%. A hard window — the old bot lost -$19.01
here (5 trades, 0 wins). This bot extracts +$8.80 from the two clean
dip-recovery legs it is built for.

## Parameter search (kit grade-local, 60 variants)
Stage 1 (24): DIP x BOUNCE_10M x TAKE_PROFIT. Stage 2 (36): DIP x TP x TRAIL.
Best plateau: **DIP=-0.012, BOUNCE_10M=0.002, TP=0.008, TRAIL=0.006** ->
+$8.80, 4 trades, WR 1.00, DD 0.57%. The result is FLAT across DIP -0.012
to -0.014 and TRAIL 0.006-0.008 (same 2 round trips) — the score does not
hang on a knife-edge parameter. Shallow DIP (-0.8%/-1.0%) loses (-$1.49 to
-$21.79) by trading the chop; TP 1.0-1.5% loses by missing the recoveries.

## Robustness
- At 2x fees, net PnL is still +$7.19 (the fee line is small: $1.61 total).
- Max drawdown 0.57% (guardrail is 25%).
- Deterministic: L1 regrade reproduced byte for byte.
- The washout mode (mode B) is untested on dev (never fires) — it is a
  straight copy of mode A's exit logic with wider parameters, and it only
  fires on a -2.5%/120m drop, which is exactly the winners' entry.

## Official kit grade-local (2026-11-17 ~16:10 WIB)
```
net PnL   8.800747 USDC  (return 0.008800747)
trading   4 trades over 1 symbols, win rate 1.000000000, max drawdown 0.005737614, exposure 0.084722222, sharpe 0.024743357, 0 rejected
fees      1.607595 USDC; at 2x fees net PnL 7.190581 USDC
guardrails met (trades ok, symbols ok, drawdown ok)
L1 regrade reproduced byte for byte
```

## Files
- `main.py` — the bot (Python 3.13, stdlib only).
- `vendor/makefun_bars.py` — kit Python shim, byte-identical to the kit's sdk/.
- `LICENSE` — MIT.
- `.makefun/owner.json` — Phantom wallet HNnvKF723WPrACxvvPg3fn5WQgrp9hq8WMtgoREcbmbK.
