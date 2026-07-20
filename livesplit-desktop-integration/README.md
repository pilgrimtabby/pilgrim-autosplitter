# LiveSplit Desktop integration (Pilgrim patch)

Vendored from [Toufool/LiveSplit.AutoSplitIntegration](https://github.com/Toufool/LiveSplit.AutoSplitIntegration) with one behavioral change for Pilgrim Autosplitter.

## Pilgrim patch

When the autosplitter prints `split` on stdout, this component treats it as **start-or-split**:

- timer not running → `Start()` (same as LiveSplit One `splitOrStart`)
- timer running → `Split()`

Pilgrim has no separate start-image file. Current Pilgrim emits `start` when the timer is not running and `split` afterward, so **stock** AutoSplit Integration works. This patch remains useful for older Pilgrim builds and for AutoSplit without a start image (outbound `split` while NotRunning).

## Installation

1. Build this project (see [`CONTRIBUTING.md`](CONTRIBUTING.md)), or use a released `LiveSplit.AutoSplitIntegration.dll` built from this folder.
2. Copy the `.dll` into `[...]\LiveSplit\Components\` (replacing Toufool’s DLL if present — same assembly name).
3. In LiveSplit: Edit Layout → Control → **AutoSplit Integration**.
4. Set **AutoSplit Path** to your `Pilgrim Autosplitter.exe` (or AutoSplit.exe).
5. Set **Profile Path** to a Pilgrim `.json` profile (or AutoSplit `.toml`).
6. Save the layout. Opening that layout launches Pilgrim with `--auto-controlled`.

## Opening / closing

Same as upstream: right-click LiveSplit → Control → Start AutoSplit / Kill AutoSplit.

## License

Upstream project license applies to this vendored tree. See the original repository for details.
