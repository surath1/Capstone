from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class AdditionInput(BaseModel):
    numbers: list[float]

@app.post("/add")
def add_numbers(input_data: AdditionInput):
    result = perform_addition(input_data.numbers)
    return {"sum": result}


def perform_addition(numbers: list[float]) -> float:
    return sum(numbers)
