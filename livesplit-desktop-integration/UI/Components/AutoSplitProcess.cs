using System;
using System.Diagnostics;
using System.IO;
using LiveSplit.Model;

namespace LiveSplit.UI.Components
{
    class AutoSplitProcess
    {
        private const string notAvailable = "N/A";

        private readonly AutoSplitIntegrationComponent component;
        private readonly AutoSplitIntegrationComponentSettings settings;
        private readonly LiveSplitState state;
        private readonly TimerModel timer;

        private int initLine = 0;

        internal Process StartupProcess { get; }
        internal Process MainProcess { get; private set; }

        private bool isRunning = false;
        internal bool IsRunning
        {
            get => isRunning;
            set
            {
                component.ContextMenuControls.Clear();

                if (value || string.IsNullOrEmpty(component.AutoSplitPath) || !File.Exists(component.AutoSplitPath))
                    settings.ButtonStartAutoSplit_Enabled = false;
                else
                {
                    settings.ButtonStartAutoSplit_Enabled = true;
                    component.ContextMenuControls.Add("Start AutoSplit", component.StartAutoSplit);
                }

                settings.ButtonKillAutoSplit_Enabled = isRunning = value;

                if (value)
                    component.ContextMenuControls.Add("Kill AutoSplit", component.KillAutoSplit);
            }
        }

        private string version = notAvailable;
        internal string Version
        {
            get => version;
            set => version = settings.LabelAutoSplitVersion_Text = value;
        }

        public AutoSplitProcess(AutoSplitIntegrationComponent component)
        {
            this.component = component;
            settings = component.Settings;
            state = component.State;
            timer = component.Timer;

            try
            {
                StartupProcess = new Process()
                {
                    StartInfo = new ProcessStartInfo()
                    {
                        FileName = component.AutoSplitPath,
                        Arguments = "--auto-controlled",
                        UseShellExecute = false,
                        RedirectStandardInput = true,
                        RedirectStandardOutput = true,
                        RedirectStandardError = true
                    }
                };

                StartupProcess.OutputDataReceived += StartupProcess_OutputDataReceived;
                StartupProcess.ErrorDataReceived += StartupProcess_ErrorDataReceived;

                StartupProcess.Start();
                StartupProcess.BeginOutputReadLine();
                StartupProcess.BeginErrorReadLine();
                IsRunning = true;
            }
            catch (Exception e)
            {
                Console.Write("Error while starting AutoSplit: ");
                Console.WriteLine(e.Message);
            }
        }

        private void StartupProcess_OutputDataReceived(object sender, DataReceivedEventArgs e)
        {
            if (string.IsNullOrEmpty(e.Data))
                return;

            if (initLine <= 1)
            {
                switch (initLine)
                {
                    case 0:
                        Version = e.Data;
                        break;
                    case 1:
                        MainProcess = Process.GetProcessById(int.Parse(e.Data));
                        MainProcess.EnableRaisingEvents = true;
                        MainProcess.Exited += MainProcess_Exited;
                        break;
                }
                initLine++;
                return;
            }

            switch (e.Data)
            {
                case Commands.KillMe:
                    Send(Commands.Kill);
                    return;
                case Commands.Start:
                    component.IgnoreNext(Commands.Start);
                    timer.Start();
                    if (component.GameTimePausing)
                        timer.InitializeGameTime();

                    settings.OnStart();
                    return;
                case Commands.Split:
                    // start-or-split (Pilgrim has no separate start image)
                    if (state.CurrentPhase == TimerPhase.NotRunning)
                    {
                        component.IgnoreNext(Commands.Start);
                        timer.Start();
                        if (component.GameTimePausing)
                            timer.InitializeGameTime();

                        settings.OnStart();
                    }
                    else
                    {
                        component.IgnoreNext(Commands.Split);
                        timer.Split();
                    }
                    return;
                case Commands.Reset:
                    component.IgnoreNext(Commands.Reset);
                    timer.Reset();
                    settings.OnReset();
                    return;
                case Commands.Pause:
                    if (component.GameTimePausing)
                        state.IsGameTimePaused ^= true;
                    else
                        timer.Pause();
                    return;
            }
        }

        private void StartupProcess_ErrorDataReceived(object sender, DataReceivedEventArgs e)
        {
            if (!string.IsNullOrEmpty(e.Data))
            {
                Console.Write("[AutoSplit] Error: ");
                Console.WriteLine(e.Data);
            }
        }

        private void MainProcess_Exited(object sender, EventArgs e)
        {
            IsRunning = false;
            Version = notAvailable;
        }

        internal void Send(string command)
        {
            if (!IsRunning)
                return;

            StartupProcess.StandardInput.WriteLine(command);
            StartupProcess.StandardInput.Flush();
        }

        internal void Close()
        {
            if (!IsRunning)
                return;

            Send(Commands.Kill);

            try
            {
                MainProcess.CloseMainWindow();
                MainProcess.CloseMainWindow();
            }

            catch { }
        }
    }
}
