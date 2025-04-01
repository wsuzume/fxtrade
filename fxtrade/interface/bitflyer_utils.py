import datetime
from dateutil import parser

######## utils for saving exec_list
import uuid


def assign_unique_name_to_executions(
    exec_list: list, dt: datetime, fstring: str = "%Y%m%d-%H%M%S-%f"
):
    xs = sorted(exec_list, key=lambda x: x["id"])

    min_id = xs[0]["id"]
    max_id = xs[-1]["id"]

    min_date = parser.isoparse(xs[0]["exec_date"])
    max_date = parser.isoparse(xs[-1]["exec_date"])

    return "_".join(
        [
            f"{min_id}",
            f"{max_id}",
            f"{min_date.strftime(fstring)}",
            f"{max_date.strftime(fstring)}",
            f"{dt.strftime(fstring)}",
            str(uuid.uuid4()),
        ]
    )
