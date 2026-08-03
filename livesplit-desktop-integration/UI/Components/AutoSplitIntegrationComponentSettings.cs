using System;
using System.IO;
using System.Reflection;
using System.Windows.Forms;
using System.Xml;
using LiveSplit.Model;

namespace LiveSplit.UI.Components
{
    public partial class AutoSplitIntegrationComponentSettings : UserControl
    {
        private readonly AutoSplitIntegrationComponent component;
        private readonly LiveSplitState state;

        internal string LabelAutoSplitVersion_Text
        {
            set => SetControlProperty(labelAutoSplitVersion, nameof(Label.Text), "AutoSplit version: " + value);
        }

        internal bool ButtonStartAutoSplit_Enabled
        {
            set => SetControlProperty(buttonStartAutoSplit, nameof(Button.Enabled), value);
        }

        internal bool ButtonKillAutoSplit_Enabled
        {
            set => SetControlProperty(buttonKillAutoSplit, nameof(Button.Enabled), value);
        }

        private void SetControlProperty<T>(Control control, string propertyName, T value) where T : IEquatable<T>
        {
            try
            {
                PropertyInfo property = control.GetType().GetProperty(propertyName);

                if (value.Equals((T)property.GetValue(control)))
                    return;

                var setProperty = new Action(() =>
                {
                    property.SetValue(control, value);
                });

                if (control.InvokeRequired)
                    Invoke(setProperty);

                else
                    setProperty();
            }

            // Control was disposed or its handle destroyed mid-update (e.g. AutoSplit
            // process events firing while the layout is being torn down on shutdown).
            catch (ObjectDisposedException) { }
            catch (InvalidOperationException) { }
        }

        internal AutoSplitIntegrationComponentSettings(AutoSplitIntegrationComponent component)
        {
            this.component = component;
            state = component.State;

            InitializeComponent();

            checkBoxGameTimePausing.Enabled = state.CurrentPhase == TimerPhase.NotRunning;
        }

        internal void OnStart() => checkBoxGameTimePausing.Enabled = false;

        internal void OnReset() => checkBoxGameTimePausing.Enabled = true;

        internal XmlNode GetSettings(XmlDocument document)
        {
            XmlElement settingsElement = document.CreateElement("Settings");

            SettingsHelper.CreateSetting(document, settingsElement, "Version", "1.8");
            SettingsHelper.CreateSetting(document, settingsElement, "AutoSplitPath", component.AutoSplitPath);
            SettingsHelper.CreateSetting(document, settingsElement, "SettingsPath", component.SettingsPath);
            SettingsHelper.CreateSetting(document, settingsElement, "GameTimePausing", component.GameTimePausing);

            return settingsElement;
        }

        internal void SetSettings(XmlNode settings)
        {
            if (((XmlElement)settings).IsEmpty)
                return;

            component.AutoSplitPath = textBoxAutoSplitPath.Text = SettingsHelper.ParseString(settings["AutoSplitPath"]);
            component.SettingsPath = textBoxSettingsPath.Text = SettingsHelper.ParseString(settings["SettingsPath"]);
            component.GameTimePausing = checkBoxGameTimePausing.Checked = SettingsHelper.ParseBool(settings["GameTimePausing"]);

            if (component.AutoSplit != null)
            {
                LabelAutoSplitVersion_Text = component.AutoSplit.Version;
                component.AutoSplit.IsRunning = component.AutoSplit.IsRunning;
            }
        }

        private void BrowseForFile(string filter, string currentPath, TextBox pathTextBox, Action<string> onSelected)
        {
            var dialog = new OpenFileDialog()
            {
                Filter = filter,
            };

            if (File.Exists(currentPath))
            {
                dialog.InitialDirectory = Path.GetDirectoryName(currentPath);
                dialog.FileName = Path.GetFileName(currentPath);
            }

            if (dialog.ShowDialog() == DialogResult.OK)
            {
                pathTextBox.Text = dialog.FileName;
                onSelected(dialog.FileName);
            }
        }

        private void ButtonAutoSplitPathBrowse_Click(object sender, EventArgs e) => BrowseForFile(
            "AutoSplit.exe|*.exe",
            component.AutoSplitPath,
            textBoxAutoSplitPath,
            path =>
            {
                component.AutoSplitPath = path;
                component.StartAutoSplit();
            });

        private void ButtonSettingsPathBrowse_Click(object sender, EventArgs e) => BrowseForFile(
            "AutoSplit Settings (*.pkl; *.toml)|*.pkl;*.toml|All files (*.*)|*.*",
            component.SettingsPath,
            textBoxSettingsPath,
            path =>
            {
                component.SettingsPath = path;
                component.LoadAutoSplitSettings();
            });

        private void ButtonStartAutoSplit_Click(object sender, EventArgs e) => component.StartAutoSplit();

        private void ButtonKillAutoSplit_Click(object sender, EventArgs e) => component.KillAutoSplit();

        private void CheckBoxGameTimePausing_CheckedChanged(object sender, EventArgs e) => component.GameTimePausing = checkBoxGameTimePausing.Checked;

        private void TextBoxAutoSplitPath_TextChanged(object sender, EventArgs e) => component.AutoSplitPath = textBoxAutoSplitPath.Text;

        private void TextBoxSettingsPath_TextChanged(object sender, EventArgs e) => component.SettingsPath = textBoxSettingsPath.Text;

    }
}
