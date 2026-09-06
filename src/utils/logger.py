from src.utils.logging import get_logger, app_logger

def setup_logger(name: str = "smart_canteen"):
    return get_logger(name, "smart_canteen.log")

logger = app_logger
