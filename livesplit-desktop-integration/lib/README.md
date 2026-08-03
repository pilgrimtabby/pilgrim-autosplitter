# Vendored LiveSplit reference assemblies

These are **third-party build-time reference assemblies from LiveSplit**, required to
compile this plugin. They are **not** redistributed with the plugin: at runtime the
LiveSplit host process provides them, so the project references them with
`<Private>false</Private>` (they are not copied into the build output).

| File                 | Purpose                                             |
| -------------------- | --------------------------------------------------- |
| `LiveSplit.exe`      | Host app assembly (`LiveSplit.UI.Components`, etc.) |
| `LiveSplit.Core.dll` | Core model/timer types (`LiveSplitState`, etc.)     |
| `UpdateManager.dll`  | Component auto-update interfaces                    |

## Pinned version

Currently pinned to **LiveSplit 1.8.37**.

## How to refresh

1. Download the latest release zip from <https://github.com/LiveSplit/LiveSplit/releases> (e.g. `LiveSplit_x.y.z.zip`).
2. Extract it and copy `LiveSplit.exe`, `LiveSplit.Core.dll`, and `UpdateManager.dll` from the archive root into this `lib/` folder, overwriting the existing files.
3. Update the **Pinned version** above.
4. Rebuild and commit.
