from server import app
from setup import database_setup, env_checkup, ram_checkup
from dotenv import load_dotenv
from orchestration.entrypoint import start_orchestration
from sentence_transformers import SentenceTransformer
from model_registry import set_model
import logging, uvicorn, time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logging.getLogger("selenium").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.WARNING)

if __name__ == "__main__":
    # Run a check for minimal configuration needs
    errors = 0
    warnings = 0
    
    # Checks hardware
    #if not ram_checkup(8) :
    #    logging.critical(f"Unable to start process, errors detected in RAM checkup")
    #    exit()

    # Check variables
    env_error, env_warning = env_checkup()
    warnings += env_warning

    if env_error:
        logging.critical(f"Unable to start process, errors detected in ENV checkup")
        exit()

    # Checks database
    if not database_setup():
        logging.critical(f"Unable to start process, errors detected in DB checkup")
        exit()

    # Sets the required libraries
    try:
        model = SentenceTransformer("all-mpnet-base-v2")
        set_model(model)
    except:
        logging.error(f"Unable to load SentenceTransformer")
        logging.critical(f"Unable to start process, errors detected in ST")
        exit()

    if warnings:
        logging.warning(f"Starting process, detected {warnings} issues")
    else:
        logging.info("Starting process with no issues")

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
