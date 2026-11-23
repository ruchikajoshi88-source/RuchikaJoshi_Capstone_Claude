from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints, model_validator


class TaskStatus(str, Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"


Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]


class TaskCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True, validate_default=True)

    title: Title
    description: str
    status: TaskStatus = TaskStatus.todo


class TaskUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    title: Title | None = None
    description: str | None = None
    status: TaskStatus | None = None

    @model_validator(mode="after")
    def reject_explicit_null(self) -> "TaskUpdate":
        # The columns are NOT NULL, so null must not be silently treated as "no change".
        for name in self.model_fields_set:
            if getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")
        return self


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    status: TaskStatus
