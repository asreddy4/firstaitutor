from . import config
from utils import log


config.set_timezone()
config.ensure_log_system()
log.info("system", f"{config.APP_NAME} booted", boot_time=config.BOOT_TIME)
