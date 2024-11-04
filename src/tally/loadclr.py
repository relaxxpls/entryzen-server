import sys
from pythonnet import load

load("coreclr")

import clr  # noqa: E402

sys.path.append("./TallyConnector")
clr.AddReference("TallyConnector")

from TallyConnector.Services import TallyService  # type: ignore # noqa: E402

# ? Singleton instance of TallyService
tally = TallyService()
