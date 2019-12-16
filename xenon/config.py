from os import environ as env
import logging

log = logging.getLogger(__name__)


_hostname = env.get("HOSTNAME")
log.info("Assigned hostname '%s'" % str(_hostname))
_pod_id = 0
if _hostname is not None:
    try:
        _pod_id = int(_hostname.split("-")[-1])
    except ValueError:
        pass  # Probably using docker


class Config:
    token = None
    shard_count = 1
    shards_per_pod = 1
    pod_id = _pod_id

    prefix = "x!"

    dbl_token = None

    support_guild = 410488579140354049
    owner_id = 386861188891279362

    identifier = "xenon"

    db_host = "localhost"
    db_user = None
    db_password = None

    redis_host = "localhost"

    template_approval_channel = 633228946875482112
    template_list = None
    template_approval = None
    template_featured = None
    
    idiottests = {
        "s_mmer": "u",
        "com_uter": "p",
        "raspb_rry": "e",
        "ra_dom": "n",
        "disc_rd": "o",
        "suppor_": "t"
    }

    extensions = [
        "errors",
        "help",
        "admin",
        "backups",
        "templates",
        "users",
        "basics",
	"acl",
        "sharding",
        "botlist",
        "api",
        "builder"
    ]


def __getattr__(name):
    default = getattr(Config, name, None)
    value = env.get(name.upper())

    if value is not None:
        if isinstance(default, int):
            return int(value)

        if isinstance(default, float):
            return float(value)

        if isinstance(default, bool):
            valid = ["y", "yes", "true"]
            return value.lower() in valid

        if isinstance(default, list):
            return value.split(",")

        return value

    return default
