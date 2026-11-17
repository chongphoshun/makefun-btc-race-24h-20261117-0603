"""BTC 24h race bot: deep-dip reversal + washout all-in. Long only, stdlib only.

ONE CONCEPT: buy only the deepest dips, and ride the snap-back. Nothing else.
The bot sits in cash almost all the time. It buys only when the price has
fallen hard against its own recent range AND the bounce has already started,
then it holds for the snap-back and gets out. No scalping, no trend-chasing,
no breakout entries, no re-entry right after a trade.

Why this shape: the previous entry (rank 775/1333, -2.66%, 14 trades) lost
because it traded too often — a shallow -0.5%/30m dip trigger plus a
breakout mode fired on every wiggle of a choppy market, and the small
losses piled up. The winners of that race did the opposite: 2-6 trades,
all-in on a washout (BTC down ~4.5%), held for the +2.4% snap-back.
This bot copies the winners' shape and removes the loser's two mistakes:
  * the dip must be DEEP (measured against the 4-hour high, not a 30-min
    wiggle), so ordinary chop never triggers a trade;
  * there is no breakout mode — in a range-bound market every breakout is
    a false one, and buying it is how you overtrade;
  * a cooldown after every trade stops the bot from re-entering the same
    chop twice in a row.

Two entry modes, both full-size (100% of cash), one position at a time:

  A) Dip reversal: the close is DIP below the highest close of the prior
     240 minutes (4 hours) AND the 10-minute return is above BOUNCE_10M
     (the bounce has started) AND the 5-minute return is above 0 (the
     bounce is still alive). Buys the start of a recovery leg after a real
     dip, not noise.
  B) Washout all-in: the 120-minute return is below WASHOUT_120M (a deep
     multi-hour capitulation) AND the 10-minute return is above
     BOUNCE_10M. Buys the washout itself. The take-profit and stops are
     wider here, because a washout's snap-back is bigger than a normal
     dip's. On the dev window this never fires (its deepest 120-min drop
     is -1.37%); it exists for the race window, where the winners' +2.4%
     snap-backs live.

Exits (per entry, whole position):
  - Take profit at TAKE_PROFIT over the entry close (mode A) or
    WASHOUT_TP (mode B). A full round trip costs ~0.4% (4 bps fee +
    2 bps slippage + ~13 bps impact per side), so the take-profit must
    clear that with room to spare.
  - Trailing stop TRAIL_STOP below the highest close since entry, so a
    snap-back that keeps running is ridden, and a fading one is exited
    near its peak.
  - Hard stop HARD_STOP below the entry close (mode A) or WASHOUT_STOP
    (mode B): the dip was not the bottom, cut it.
  - Cooldown: after any sell, no new buy for COOLDOWN bars.

Protocol: agent-fun/bars-replay/v1 via the kit's Python shim (vendored
byte-identical under vendor/). One reply per batch, deterministic: only
float arithmetic on the bar closes, no clock, no randomness, no I/O.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))

import makefun_bars

SYMBOL = "CBBTC"

# --- entry parameters ---
RANGE_BARS = 240      # mode A: rolling high window (bars)
DIP = -0.012          # mode A: close DIP below the 240-bar high
BOUNCE_10M = 0.002    # both modes: 10-min return above this
BOUNCE_5M = 0.0       # mode A: 5-min return above this
WASHOUT_120M = -0.025  # mode B: 120-min return below this
COOLDOWN = 60         # bars to wait after a sell before the next buy

# --- exit parameters ---
TAKE_PROFIT = 0.008   # mode A: +0.8% over the entry close
TRAIL_STOP = 0.006    # mode A: 0.6% below the peak close since entry
HARD_STOP = 0.008     # mode A: 0.8% below the entry close
WASHOUT_TP = 0.020    # mode B: +2.0% over the entry close
WASHOUT_TRAIL = 0.010  # mode B: 1.0% below the peak close since entry
WASHOUT_STOP = 0.012  # mode B: 1.2% below the entry close

MAX_SLIPPAGE_BPS = 200  # 2%: the largest 1-min move in the dev window is 66 bps


class Bot:
    def __init__(self):
        self.closes = []        # closes (float USD) in bar order, fresh bars only
        self.entry_close = None  # close of the bar the current position was decided on
        self.peak = None        # highest close since entry
        self.mode = None        # "A" (dip reversal) or "B" (washout)
        self.pending = None     # (entry_close, mode) of a buy sent, awaiting confirmation
        self.cooldown_until = -1  # seq (bar index) before which no new buy

    def _ret(self, bars_back):
        """Return over the last `bars_back` bars, or None without enough history."""
        n = len(self.closes)
        if n <= bars_back:
            return None
        now = self.closes[-1]
        then = self.closes[-1 - bars_back]
        return now / then - 1.0

    def _high(self, bars_back):
        """Highest close of the prior `bars_back` closes, excluding the current one."""
        window = self.closes[-1 - bars_back:-1]
        if len(window) < bars_back:
            return None
        return max(window)

    def on_batch(self, state, batch):
        fresh = any(b["symbol"] == SYMBOL for b in batch["bars"])
        if fresh:
            self.closes.append(float(state.close(SYMBOL)))
        if state.warming_up or not fresh:
            return []

        close = self.closes[-1]
        held = state.positions.get(SYMBOL)

        # Confirm a pending buy once the position actually appears; drop it
        # if the buy was rejected (no position on the next batch).
        if held is not None:
            if self.pending is not None:
                self.entry_close, self.mode = self.pending
                self.peak = close
                self.pending = None
            if self.entry_close is None:
                self.entry_close = close
                self.mode = "A"
                self.peak = close
        else:
            if self.entry_close is not None:
                # A position just closed: start the cooldown.
                self.cooldown_until = len(self.closes) + COOLDOWN
            self.entry_close = None
            self.peak = None
            self.mode = None
            self.pending = None

        if held is None:
            return self._maybe_buy(state, close)

        # --- holding: exits ---
        if close > self.peak:
            self.peak = close
        entry = self.entry_close
        if self.mode == "B":
            tp, trail, stop = WASHOUT_TP, WASHOUT_TRAIL, WASHOUT_STOP
        else:
            tp, trail, stop = TAKE_PROFIT, TRAIL_STOP, HARD_STOP
        if close >= entry * (1.0 + tp):
            return self._sell(state)
        if close <= self.peak * (1.0 - trail):
            return self._sell(state)
        if close <= entry * (1.0 - stop):
            return self._sell(state)
        return []

    def _maybe_buy(self, state, close):
        if len(self.closes) < self.cooldown_until:
            return []
        r10 = self._ret(10)
        if r10 is None or r10 <= BOUNCE_10M:
            return []
        mode = None
        # Mode B first: a deep washout outranks an ordinary dip.
        r120 = self._ret(120)
        if r120 is not None and r120 < WASHOUT_120M:
            mode = "B"
        else:
            hi = self._high(RANGE_BARS)
            r5 = self._ret(5)
            if (hi is not None and r5 is not None
                    and close / hi - 1.0 < DIP and r5 > BOUNCE_5M):
                mode = "A"
        if mode is None:
            return []
        notional = min(state.cash, state.weight_room(SYMBOL))
        if notional < int(state.hello["fees"]["min_notional_quote_units"]):
            return []
        self.pending = (close, mode)
        return [{"side": "buy", "symbol": SYMBOL,
                 "notional_quote_units": notional,
                 "max_slippage_bps": MAX_SLIPPAGE_BPS}]

    def _sell(self, state):
        held = state.positions.get(SYMBOL)
        if held is None or held.qty <= 0:
            return []
        return [{"side": "sell", "symbol": SYMBOL, "qty": held.qty,
                 "max_slippage_bps": MAX_SLIPPAGE_BPS}]


def main():
    bot = Bot()
    makefun_bars.run(bot.on_batch)


if __name__ == "__main__":
    main()
