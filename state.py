from typing import Annotated, TypedDict

def merge_dicts(existing: dict, new: dict) -> dict:
    return {**existing, **new}

class GraphState(TypedDict):
    input_text : str
    summary : str
    mcqs : str
    error : str
    tokens: Annotated[dict, merge_dicts]


