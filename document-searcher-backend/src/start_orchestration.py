from dotenv import load_dotenv
import logging
load_dotenv()

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    from orchestration.entrypoint import start_orchestration
    start_orchestration()
