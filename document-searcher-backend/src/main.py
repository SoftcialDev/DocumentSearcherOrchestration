from server import app
from setup import database_setup, env_checkup, ram_checkup
from dotenv import load_dotenv
from orchestration.entrypoint import start_orchestration
from sentence_transformers import SentenceTransformer
from model_registry import set_model
import logging, uvicorn

load_dotenv()
logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    # Run a check for minimal configuration needs
    ram_status = ram_checkup(8)
    env_error, env_warning = env_checkup()

    if not env_error:
        db_status = database_setup()

    errors = env_error + ram_status
    if errors:
        logging.critical(f"Unable to start process, detected {errors} errors")
        exit()

    warnings = env_warning
    if warnings:
        logging.warning(f"Starting process, detected {warnings} issues")
    else:
        logging.info("Starting process with no issues")

    # Sets the required libraries
    model = SentenceTransformer("all-mpnet-base-v2")
    set_model(model)

    # Start the orchestration process, does not require Flask to be running
    start_orchestration()
    uvicorn.run(
        "server:app", 
        host="0.0.0.0", 
        port=5000, 
        reload=True,
        reload_dirs=[".", "modules"],
        reload_includes=["*.py", "*.env"],
        reload_excludes=["*.pyc", "node_modules/*"],
    ) 