import sys
from pythonnet import load

load("coreclr")

import clr  # noqa: E402

sys.path.append("./TallyConnector")
clr.AddReference("TallyConnector")
