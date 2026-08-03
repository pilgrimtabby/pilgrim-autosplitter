using System;
using System.Drawing;
using System.IO;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Windows.Forms;
using LiveSplit.Model;
using LiveSplit.UI.Components;

namespace LiveSplit.PreviewTool
{
    // Renders AutoSplitIntegrationComponentSettings without a live LiveSplit host.
    // The component subscribes to LiveSplitState events in its ctor, so a real state is
    // built; the settings ctor only reads state.CurrentPhase (defaults to NotRunning).
    internal static class Program
    {
        [STAThread]
        private static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);

            LiveSplitState state = MakeState();
            var component = new AutoSplitIntegrationComponent(state);

            // Settings is internal; the tool is a separate assembly, so reach it by reflection.
            var settings = (Control)typeof(AutoSplitIntegrationComponent)
                .GetProperty("Settings", BindingFlags.Instance | BindingFlags.NonPublic)!
                .GetValue(component)!;

            using var form = new Form
            {
                ClientSize = settings.Size,
                Text = "AutoSplit Integration Settings (preview)",
                StartPosition = FormStartPosition.CenterScreen,
                Icon = TryLoadLiveSplitIcon() ?? SystemIcons.Application,
            };
            form.Controls.Add(settings);
            Application.Run(form);
        }

        // LiveSplit.exe is copied next to this exe (see the vendored Reference's Private=true), so the
        // window icon can be pulled from it at runtime instead of vendoring a separate .ico. Use shell32's
        // ExtractIconEx rather than Icon.ExtractAssociatedIcon: the latter returns a generic placeholder
        // under wine's Mono, while ExtractIconEx reads the real embedded icon on both Windows and wine.
        // On wine the transparent corners render black (the HICON's 32-bit alpha is dropped); Windows is
        // unaffected. Accepted as cosmetic for this preview-only tool.
        private static Icon? TryLoadLiveSplitIcon()
        {
            var liveSplitExePath = Path.Combine(AppContext.BaseDirectory, "LiveSplit.exe");
            var largeIcons = new IntPtr[1];
            if (ExtractIconEx(liveSplitExePath, 0, largeIcons, null, 1) == 0 || largeIcons[0] == IntPtr.Zero)
                return null;

            try
            {
                // Icon.FromHandle does not own the handle, so clone to a managed icon before freeing it.
                return (Icon)Icon.FromHandle(largeIcons[0]).Clone();
            }
            finally
            {
                DestroyIcon(largeIcons[0]);
            }
        }

        [DllImport("shell32.dll", CharSet = CharSet.Unicode)]
        private static extern uint ExtractIconEx(string fileName, int iconIndex, IntPtr[] largeIcons, IntPtr[]? smallIcons, uint iconCount);

        [DllImport("user32.dll")]
        private static extern bool DestroyIcon(IntPtr handle);

        private static LiveSplitState MakeState()
        {
            // LiveSplitState(run, form, layout, layoutSettings, settings). Only CurrentPhase is
            // read here (enum default NotRunning), so nulls are fine; fall back to an
            // uninitialized instance if a future ctor change starts dereferencing them.
            object?[] args = [null, null, null, null, null];
            return (LiveSplitState)Activator.CreateInstance(typeof(LiveSplitState), args);

        }
    }
}
