"""Constants for the Grandstream GDMS Networking integration."""

DOMAIN = "grandstream_gdms"

CONF_BASE_URL = "base_url"
CONF_APP_ID = "app_id"
CONF_SECRET_KEY = "secret_key"
CONF_NETWORK_ID = "network_id"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_BASE_URL = "https://www.gdms.cloud"
DEFAULT_SCAN_INTERVAL = 60

REGIONAL_SERVERS = {
    "https://www.gdms.cloud": "GDMS Global / US (www.gdms.cloud)",
    "https://eu.gdms.cloud": "GDMS Europe (eu.gdms.cloud)",
    "https://www.gwn.cloud": "GWN.Cloud Global / US (www.gwn.cloud)",
    "https://eu.gwn.cloud": "GWN.Cloud Europe (eu.gwn.cloud)",
}

API_TOKEN_PATH = "/oapi/oauth/token"
API_NETWORK_LIST_PATH = "/oapi/v1.0.0/network/list"
API_AP_LIST_PATH = "/oapi/v1.0.0/ap/list"
API_CLIENT_LIST_PATH = "/oapi/v1.0.0/client/list"
