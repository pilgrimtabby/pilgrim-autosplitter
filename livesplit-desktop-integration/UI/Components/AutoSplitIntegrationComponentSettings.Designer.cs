using System.Windows.Forms;

namespace LiveSplit.UI.Components
{
    partial class AutoSplitIntegrationComponentSettings
    {
        /// <summary> 
        /// Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary> 
        /// Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Component Designer generated code

        /// <summary> 
        /// Required method for Designer support - do not modify 
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            this.labelAutoSplitPath = new System.Windows.Forms.Label();
            this.buttonAutoSplitPathBrowse = new System.Windows.Forms.Button();
            this.textBoxAutoSplitPath = new System.Windows.Forms.TextBox();
            this.tableLayoutPanel1 = new System.Windows.Forms.TableLayoutPanel();
            this.buttonSettingsPathBrowse = new System.Windows.Forms.Button();
            this.textBoxSettingsPath = new System.Windows.Forms.TextBox();
            this.labelSettingsPath = new System.Windows.Forms.Label();
            this.flowLayoutPanel1 = new System.Windows.Forms.FlowLayoutPanel();
            this.buttonStartAutoSplit = new System.Windows.Forms.Button();
            this.buttonKillAutoSplit = new System.Windows.Forms.Button();
            this.labelAutoSplitVersion = new System.Windows.Forms.Label();
            this.labelAutoSplit = new System.Windows.Forms.Label();
            this.labelPausing = new System.Windows.Forms.Label();
            this.checkBoxGameTimePausing = new System.Windows.Forms.CheckBox();
            this.tableLayoutPanel1.SuspendLayout();
            this.flowLayoutPanel1.SuspendLayout();
            this.SuspendLayout();
            // 
            // labelAutoSplitPath
            // 
            this.labelAutoSplitPath.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Left | System.Windows.Forms.AnchorStyles.Right)));
            this.labelAutoSplitPath.AutoSize = true;
            this.labelAutoSplitPath.Location = new System.Drawing.Point(3, 7);
            this.labelAutoSplitPath.Name = "labelAutoSplitPath";
            this.labelAutoSplitPath.Size = new System.Drawing.Size(77, 13);
            this.labelAutoSplitPath.TabIndex = 0;
            this.labelAutoSplitPath.Text = "AutoSplit Path:";
            // 
            // buttonAutoSplitPathBrowse
            // 
            this.buttonAutoSplitPathBrowse.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Left | System.Windows.Forms.AnchorStyles.Right)));
            this.buttonAutoSplitPathBrowse.AutoSize = true;
            this.buttonAutoSplitPathBrowse.Location = new System.Drawing.Point(386, 3);
            this.buttonAutoSplitPathBrowse.Name = "buttonAutoSplitPathBrowse";
            this.buttonAutoSplitPathBrowse.Size = new System.Drawing.Size(73, 22);
            this.buttonAutoSplitPathBrowse.TabIndex = 2;
            this.buttonAutoSplitPathBrowse.Text = "Browse...";
            this.buttonAutoSplitPathBrowse.UseVisualStyleBackColor = true;
            this.buttonAutoSplitPathBrowse.Click += new System.EventHandler(this.ButtonAutoSplitPathBrowse_Click);
            // 
            // textBoxAutoSplitPath
            // 
            this.textBoxAutoSplitPath.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Left | System.Windows.Forms.AnchorStyles.Right)));
            this.textBoxAutoSplitPath.Location = new System.Drawing.Point(86, 4);
            this.textBoxAutoSplitPath.Name = "textBoxAutoSplitPath";
            this.textBoxAutoSplitPath.Size = new System.Drawing.Size(294, 20);
            this.textBoxAutoSplitPath.TabIndex = 1;
            this.textBoxAutoSplitPath.TextChanged += new System.EventHandler(this.TextBoxAutoSplitPath_TextChanged);
            // 
            // tableLayoutPanel1
            // 
            this.tableLayoutPanel1.ColumnCount = 3;
            this.tableLayoutPanel1.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle());
            this.tableLayoutPanel1.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Absolute, 300F));
            this.tableLayoutPanel1.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Absolute, 79F));
            this.tableLayoutPanel1.Controls.Add(this.buttonSettingsPathBrowse, 2, 1);
            this.tableLayoutPanel1.Controls.Add(this.textBoxSettingsPath, 1, 1);
            this.tableLayoutPanel1.Controls.Add(this.labelSettingsPath, 0, 1);
            this.tableLayoutPanel1.Controls.Add(this.textBoxAutoSplitPath, 1, 0);
            this.tableLayoutPanel1.Controls.Add(this.flowLayoutPanel1, 1, 2);
            this.tableLayoutPanel1.Controls.Add(this.labelAutoSplit, 0, 2);
            this.tableLayoutPanel1.Controls.Add(this.labelPausing, 0, 3);
            this.tableLayoutPanel1.Controls.Add(this.checkBoxGameTimePausing, 1, 3);
            this.tableLayoutPanel1.Controls.Add(this.buttonAutoSplitPathBrowse, 2, 0);
            this.tableLayoutPanel1.Controls.Add(this.labelAutoSplitPath, 0, 0);
            this.tableLayoutPanel1.Dock = System.Windows.Forms.DockStyle.Fill;
            this.tableLayoutPanel1.Location = new System.Drawing.Point(7, 7);
            this.tableLayoutPanel1.Name = "tableLayoutPanel1";
            this.tableLayoutPanel1.RowCount = 4;
            this.tableLayoutPanel1.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Absolute, 28F));
            this.tableLayoutPanel1.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Absolute, 28F));
            this.tableLayoutPanel1.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Absolute, 28F));
            this.tableLayoutPanel1.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Absolute, 28F));
            this.tableLayoutPanel1.Size = new System.Drawing.Size(462, 111);
            this.tableLayoutPanel1.TabIndex = 0;
            // 
            // buttonSettingsPathBrowse
            // 
            this.buttonSettingsPathBrowse.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Left | System.Windows.Forms.AnchorStyles.Right)));
            this.buttonSettingsPathBrowse.AutoSize = true;
            this.buttonSettingsPathBrowse.Location = new System.Drawing.Point(386, 31);
            this.buttonSettingsPathBrowse.Name = "buttonSettingsPathBrowse";
            this.buttonSettingsPathBrowse.Size = new System.Drawing.Size(73, 22);
            this.buttonSettingsPathBrowse.TabIndex = 5;
            this.buttonSettingsPathBrowse.Text = "Browse...";
            this.buttonSettingsPathBrowse.UseVisualStyleBackColor = true;
            this.buttonSettingsPathBrowse.Click += new System.EventHandler(this.ButtonSettingsPathBrowse_Click);
            // 
            // textBoxSettingsPath
            // 
            this.textBoxSettingsPath.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Left | System.Windows.Forms.AnchorStyles.Right)));
            this.textBoxSettingsPath.Location = new System.Drawing.Point(86, 32);
            this.textBoxSettingsPath.Name = "textBoxSettingsPath";
            this.textBoxSettingsPath.Size = new System.Drawing.Size(294, 20);
            this.textBoxSettingsPath.TabIndex = 4;
            this.textBoxSettingsPath.TextChanged += new System.EventHandler(this.TextBoxSettingsPath_TextChanged);
            // 
            // labelSettingsPath
            // 
            this.labelSettingsPath.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Left | System.Windows.Forms.AnchorStyles.Right)));
            this.labelSettingsPath.AutoSize = true;
            this.labelSettingsPath.Location = new System.Drawing.Point(3, 35);
            this.labelSettingsPath.Name = "labelSettingsPath";
            this.labelSettingsPath.Size = new System.Drawing.Size(77, 13);
            this.labelSettingsPath.TabIndex = 3;
            this.labelSettingsPath.Text = "Settings Path:";
            // 
            // flowLayoutPanel1
            // 
            this.flowLayoutPanel1.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Left | System.Windows.Forms.AnchorStyles.Right)));
            this.flowLayoutPanel1.AutoSize = true;
            this.tableLayoutPanel1.SetColumnSpan(this.flowLayoutPanel1, 2);
            this.flowLayoutPanel1.Controls.Add(this.buttonStartAutoSplit);
            this.flowLayoutPanel1.Controls.Add(this.buttonKillAutoSplit);
            this.flowLayoutPanel1.Controls.Add(this.labelAutoSplitVersion);
            this.flowLayoutPanel1.Location = new System.Drawing.Point(83, 56);
            this.flowLayoutPanel1.Margin = new System.Windows.Forms.Padding(0);
            this.flowLayoutPanel1.Name = "flowLayoutPanel1";
            this.flowLayoutPanel1.Size = new System.Drawing.Size(379, 28);
            this.flowLayoutPanel1.TabIndex = 10;
            // 
            // buttonStartAutoSplit
            // 
            this.buttonStartAutoSplit.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Left | System.Windows.Forms.AnchorStyles.Right)));
            this.buttonStartAutoSplit.Enabled = false;
            this.buttonStartAutoSplit.Location = new System.Drawing.Point(3, 3);
            this.buttonStartAutoSplit.Name = "buttonStartAutoSplit";
            this.buttonStartAutoSplit.Size = new System.Drawing.Size(100, 23);
            this.buttonStartAutoSplit.TabIndex = 7;
            this.buttonStartAutoSplit.Text = "Start AutoSplit";
            this.buttonStartAutoSplit.UseVisualStyleBackColor = true;
            this.buttonStartAutoSplit.Click += new System.EventHandler(this.ButtonStartAutoSplit_Click);
            // 
            // buttonKillAutoSplit
            // 
            this.buttonKillAutoSplit.Enabled = false;
            this.buttonKillAutoSplit.Location = new System.Drawing.Point(109, 3);
            this.buttonKillAutoSplit.Name = "buttonKillAutoSplit";
            this.buttonKillAutoSplit.Size = new System.Drawing.Size(100, 23);
            this.buttonKillAutoSplit.TabIndex = 8;
            this.buttonKillAutoSplit.Text = "Kill AutoSplit";
            this.buttonKillAutoSplit.UseVisualStyleBackColor = true;
            this.buttonKillAutoSplit.Click += new System.EventHandler(this.ButtonKillAutoSplit_Click);
            // 
            // labelAutoSplitVersion
            // 
            this.labelAutoSplitVersion.Anchor = System.Windows.Forms.AnchorStyles.Right;
            this.labelAutoSplitVersion.Location = new System.Drawing.Point(215, 6);
            this.labelAutoSplitVersion.Margin = new System.Windows.Forms.Padding(3);
            this.labelAutoSplitVersion.Name = "labelAutoSplitVersion";
            this.labelAutoSplitVersion.Size = new System.Drawing.Size(161, 17);
            this.labelAutoSplitVersion.TabIndex = 9;
            this.labelAutoSplitVersion.Text = "AutoSplit Version: N/A";
            this.labelAutoSplitVersion.TextAlign = System.Drawing.ContentAlignment.MiddleRight;
            // 
            // labelAutoSplit
            // 
            this.labelAutoSplit.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Left | System.Windows.Forms.AnchorStyles.Right)));
            this.labelAutoSplit.AutoSize = true;
            this.labelAutoSplit.Location = new System.Drawing.Point(3, 63);
            this.labelAutoSplit.Name = "labelAutoSplit";
            this.labelAutoSplit.Size = new System.Drawing.Size(77, 13);
            this.labelAutoSplit.TabIndex = 6;
            this.labelAutoSplit.Text = "AutoSplit:";
            // 
            // labelPausing
            // 
            this.labelPausing.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Left | System.Windows.Forms.AnchorStyles.Right)));
            this.labelPausing.AutoSize = true;
            this.labelPausing.Location = new System.Drawing.Point(3, 91);
            this.labelPausing.Name = "labelPausing";
            this.labelPausing.Size = new System.Drawing.Size(77, 13);
            this.labelPausing.TabIndex = 11;
            this.labelPausing.Text = "Pausing:";
            // 
            // checkBoxGameTimePausing
            // 
            this.checkBoxGameTimePausing.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Left | System.Windows.Forms.AnchorStyles.Right)));
            this.checkBoxGameTimePausing.AutoSize = true;
            this.tableLayoutPanel1.SetColumnSpan(this.checkBoxGameTimePausing, 2);
            this.checkBoxGameTimePausing.Location = new System.Drawing.Point(86, 89);
            this.checkBoxGameTimePausing.Name = "checkBoxGameTimePausing";
            this.checkBoxGameTimePausing.Size = new System.Drawing.Size(373, 17);
            this.checkBoxGameTimePausing.TabIndex = 12;
            this.checkBoxGameTimePausing.Text = "Pause Game Time only (this will disallow manual unpausing)";
            this.checkBoxGameTimePausing.UseVisualStyleBackColor = true;
            this.checkBoxGameTimePausing.CheckedChanged += new System.EventHandler(this.CheckBoxGameTimePausing_CheckedChanged);
            // 
            // AutoSplitIntegrationComponentSettings
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(6F, 13F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.Controls.Add(this.tableLayoutPanel1);
            this.Name = "AutoSplitIntegrationComponentSettings";
            this.Padding = new System.Windows.Forms.Padding(7);
            this.Size = new System.Drawing.Size(476, 125);
            this.tableLayoutPanel1.ResumeLayout(false);
            this.tableLayoutPanel1.PerformLayout();
            this.flowLayoutPanel1.ResumeLayout(false);
            this.ResumeLayout(false);

        }

        private Label labelAutoSplitPath;
        private Button buttonAutoSplitPathBrowse;
        private TextBox textBoxAutoSplitPath;
        private FlowLayoutPanel flowLayoutPanel1;
        private Label labelAutoSplitVersion;
        private TableLayoutPanel tableLayoutPanel1;
        private Button buttonStartAutoSplit;
        private Label labelAutoSplit;
        private Button buttonKillAutoSplit;
        private Label labelPausing;
        private CheckBox checkBoxGameTimePausing;
        private Label labelSettingsPath;
        private Button buttonSettingsPathBrowse;
        private TextBox textBoxSettingsPath;
    }

    #endregion
}