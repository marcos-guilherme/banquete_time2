from pydantic import BaseModel
from typing import Optional, List

class InputData(BaseModel):
    text: str
    metadata: Optional[dict] = None