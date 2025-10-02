from server import app
from setup import database_setup, env_checkup, ram_checkup
from dotenv import load_dotenv
from orchestration.entrypoint import start_orchestration
from sentence_transformers import SentenceTransformer
from model_registry import set_model
from modules.logs import write_line, write_block
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
    #if not ram_checkup(8, logs) :
    #    write_line("---CRITICAL---")
    #    logging.critical(f"Unable to start process, errors detected in RAM checkup")
    #    write_line("---CRITICAL---")
    #    exit()

    # Check variables
    env_error, env_warning = env_checkup()
    warnings += env_warning

    if env_error:
        write_line("---CRITICAL---")
        write_line(f"Unable to start process, errors detected in ENV checkup")
        write_line("---CRITICAL---")
        exit()

    # Checks database
    if not database_setup():
        write_line("---CRITICAL---")
        write_line(f"Unable to start process, errors detected in DB checkup")
        write_line("---CRITICAL---")
        exit()

    # Sets the required libraries
    try:
        model = SentenceTransformer("all-mpnet-base-v2")
        set_model(model)
    except:
        write_line("---CRITICAL---")
        write_line(f"Unable to load SentenceTransformer")
        write_line(f"Unable to start process, errors detected in ST")
        write_line("---CRITICAL---")
        exit()

    if warnings:
        write_line("---WARNING---")
        write_line(f"Starting process, detected {warnings} issues")
        write_line("---WARNING---")
    else:
        write_line("Starting process with no issues")

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
