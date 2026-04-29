import logging
import sys

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)

auth_log = logging.getLogger("tecball.auth")
admin_log = logging.getLogger("tecball.admin")
bets_log = logging.getLogger("tecball.bets")
