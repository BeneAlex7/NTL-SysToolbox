from modules.audit import run,eol_csv,scan_network
from core.config_loader import load_config
from core.logger import NTL_Logger
import sys

logger = NTL_Logger()
config = load_config()
resultat = run(config)
exit_code = logger.log(resultat)

# Test list eol from csv
resultat = eol_csv(config)
exit_code = logger.log(resultat)

resultat = scan_network(config)
exit_code = logger.log(resultat)