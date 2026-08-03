# Contributing guidelines

## Style guide and formatting

Avoid manually wrapping lines in markdown files.

The project is setup to automatically configure VSCode with the proper extensions and settings. Fixers and formatters will be run on save.\
Project configurations for other IDEs are welcome.

You can run `dotnet format` to automatically format csharp files according to `.editorconfig`.

<!-- TODO: The CI will automatically fix and commit any autofixable issue your changes may have. -->

## Compiling

Requirements:

- The [.NET SDK 10.x](https://dotnet.microsoft.com/download)
- The [.NET Framework 4.8.1 Developer Pack](https://dotnet.microsoft.com/download/dotnet-framework/net481)
- Optionally [Visual Studio 2022](https://visualstudio.microsoft.com/vs)

Then either:

- Run `dotnet build --configuration Release`, or
- Open `LiveSplit.AutoSplitIntegration.csproj` in Visual Studio 2022 and build.

The LiveSplit assemblies needed to compile (`LiveSplit.exe`, and dlls) are vendored under [`lib/`](lib/). See [`lib/README.md`](lib/README.md) to refresh them.

## Previewing the settings UI

The component's settings panel is a WinForms `UserControl`. To preview visual changes without installing the component into a real LiveSplit, run `scripts/preview-settings.ps1`. It builds [`tools/PreviewSettings`](tools/PreviewSettings/) (a throwaway .NET WinExe that reads the component's `Settings` control by reflection and feeds it a minimal `LiveSplitState`) and launches it. Buttons are inert since there is no host.

The tool works on Windows directly. On Linux it runs under [wine](https://www.winehq.org/), whose bundled Mono renders WinForms through wine's own graphics stack, so text and layout match Windows and the real LiveSplit host. Native [Mono](https://www.mono-project.com/) is intentionally not used: it renders quite differently via `libgdiplus`, on top of having known [rendering bug](https://github.com/TASEmulators/BizHawk/issues/4469), which defeats the purpose of a visual preview.

## Changelog

If your change is user-facing, add a `<change>` line to the **`version="0.0.0"`** `<update>` block in [`update.LiveSplit.AutoSplitIntegration.xml`](update.LiveSplit.AutoSplitIntegration.xml), in the same PR. Entries there reach users only once promoted into a real version at release.

Do not modify `version="0.0.0"` or the `<Version>` in [`LiveSplit.AutoSplitIntegration.csproj`](LiveSplit.AutoSplitIntegration.csproj) (fallback for local builds). The real release version comes from the **manifest**: the newest non-`0.0.0` `<update version>` is what gets released automatically by [.github/release.yml](.github/release.yml).

## Releasing a new version

We use LiveSplit's built-in component auto-updater: LiveSplit polls the factory's `XMLURL`, and offers an update when a listed `<update version="...">` is newer than the installed component's `Version`.

To publish a release, run `./scripts/bump-version.ps1 X.X.X` with the new version, then commit and push to `main`.

The **Release** workflow then validates the manifest, builds with the manifest's version, and publishes a `vX.Y.Z` GitHub release+tag with the `.dll` + `.pdb` attached.

If a release fails partway, just re-run it from [`Actions > Release`](https://github.com/Toufool/LiveSplit.AutoSplitIntegration/actions/workflows/build.yml)`> Run workflow` after fixing the issue. The tag is only created on a successful publish, so there is nothing to delete or clean up first.
