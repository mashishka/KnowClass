import re
from pathlib import Path

path_to_tables = "../../data_utils/imp/tables.py"


text = Path(path_to_tables).read_text()

# add cascade to relations with lowercase in first symbol back_populates (uppercase == name of table)
text = re.sub("(back_populates='[a-z][^']*')", '\\1, cascade="all, delete, delete-orphan"', text)
# don't work with enum constraints...
text = text.replace(
    "result_type: Mapped[Optional[str]] = mapped_column(Enum)",
    "result_type: Mapped[Optional[str]] = mapped_column(Text, CheckConstraint(\"result_type in ('probability', 'confidence')\"))",
)

Path(path_to_tables).write_text(text)
