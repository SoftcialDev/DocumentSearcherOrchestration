from fastapi import APIRouter

router = APIRouter(prefix="/api/test", tags=["admin"])

router.get("/execute")
def execute():
    execute_text()
    return "Test executed"

def execute_text():
    pass