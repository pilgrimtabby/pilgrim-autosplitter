namespace LiveSplit.UI.Components
{
    /// <summary>
    /// Wire-protocol tokens exchanged over stdio with the AutoSplit process
    /// (AutoSplit's <c>--auto-controlled</c> mode).
    /// </summary>
    internal static class Commands
    {
        // Sent to and received from AutoSplit.
        internal const string Start = "start";
        internal const string Split = "split";
        internal const string Reset = "reset";

        // Only received from AutoSplit.
        internal const string KillMe = "killme";
        internal const string Pause = "pause";

        // Only sent to AutoSplit.
        internal const string Skip = "skip";
        internal const string Undo = "undo";
        internal const string Kill = "kill";

        // Sent to AutoSplit with the settings file path as an argument.
        internal static string Settings(string path) => "settings|" + path;
    }
}
