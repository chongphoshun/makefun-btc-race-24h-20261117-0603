[![make.fun](https://make.fun/badge/btc-race-24h-20261117-0603.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603)
[![rank](https://make.fun/badge/btc-race-24h-20261117-0603/chongphoshun/makefun-btc-race-24h-20261117-0603/rank.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603)
[![reward](https://make.fun/badge/btc-race-24h-20261117-0603/chongphoshun/makefun-btc-race-24h-20261117-0603/reward.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603)

# BTC 24h race bot — buy only the deepest dips, ride the snap-back

Entry for the [make.fun bounty btc-race-24h-20261117-0603](https://make.fun/bounty/btc-race-24h-20261117-0603):
race a BTC trading bot live for 24 hours on Coinbase Wrapped BTC (cbBTC) vs USDC.

## The one idea

Buy only the deepest dips, and ride the snap-back. Nothing else. The bot sits
in cash almost all the time, buys only when the price has fallen hard against
its own recent range AND the bounce has already started, then holds for the
snap-back and gets out. No scalping, no trend-chasing, no breakout entries,
no re-entry right after a trade.

The previous entry in this series lost (rank 775/1333, -2.66%, 14 trades)
because it traded too often — a shallow dip trigger plus a breakout mode fired
on every wiggle of a choppy market. The winners did the opposite: 2-6 trades,
all-in on a washout, held for the snap-back. This bot copies the winners'
shape and removes the loser's two mistakes: the dip must be DEEP, and there is
no breakout mode.

## Strategy

- **Dip reversal:** close 1.2% below the highest close of the prior 240 min
  AND 10-min return above +0.2% AND 5-min return above 0. Full size.
  Exit: take-profit +0.8%, trailing stop 0.6% below the peak, hard stop 0.8%,
  60-bar cooldown after every sell.
- **Washout all-in:** 120-min return below -2.5% AND 10-min return above
  +0.2%. Wider exits (TP +2.0%, trail 1.0%, stop 1.2%). For the race window,
  where the big snap-backs live.

## Dev result (kit grade-local, 2026-11-17)

- Net PnL **+8.80 USDC** (gate: > $0) — 4 trades, win rate **1.00**,
  max drawdown **0.57%**, 0 rejected orders.
- The dev window is flat (+0.49%); the old bot lost -$19.01 on it.
- At 2x fees the net is still +$7.19. L1 regrade byte-identical.

See [TEST-REPORT.md](TEST-REPORT.md) for the full parameter search (60 variants).

## Run

Python 3.13, stdlib only. The kit's Python shim is vendored byte-identical
under `vendor/`. `main.py` is the entrypoint; it speaks
`agent-fun/bars-replay/v1` through the shim.

## License

MIT.
