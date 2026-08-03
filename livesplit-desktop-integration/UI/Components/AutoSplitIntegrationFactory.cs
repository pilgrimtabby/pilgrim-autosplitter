using System;
using LiveSplit.Model;
using LiveSplit.UI.Components;

[assembly: ComponentFactory(typeof(AutoSplitIntegrationFactory))]

namespace LiveSplit.UI.Components
{
    public class AutoSplitIntegrationFactory : IComponentFactory
    {
        public string ComponentName => "AutoSplit Integration";

        public string Description => "Directly connects AutoSplit with LiveSplit.";

        public ComponentCategory Category => ComponentCategory.Control;

        public Version Version => GetType().Assembly.GetName().Version;

        public string UpdateName => ComponentName;

        public string UpdateURL => "https://github.com/Toufool/LiveSplit.AutoSplitIntegration/releases/";

        public string XMLURL => "https://raw.githubusercontent.com/Toufool/LiveSplit.AutoSplitIntegration/main/update.LiveSplit.AutoSplitIntegration.xml";

        public IComponent Create(LiveSplitState state) => new AutoSplitIntegrationComponent(state);
    }
}
