from modules.audit import run
from core.config_loader import load_config
from core.logger import NTL_Logger
import sys

logger = NTL_Logger()
config = load_config()
resultat = run(config)
exit_code = logger.log(resultat)
