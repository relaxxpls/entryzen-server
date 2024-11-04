from datetime import datetime
from System import DateTime  # type: ignore # noqa: E402
from TallyConnector.Core.Converters.XMLConverterHelpers import TallyDate  # type: ignore # noqa: E402


def convert_to_tally_date(date: datetime | str) -> TallyDate:
    if isinstance(date, str):
        date = datetime.strptime(date, "%d/%m/%Y")
    return TallyDate(DateTime(date.year, date.month, date.day))
