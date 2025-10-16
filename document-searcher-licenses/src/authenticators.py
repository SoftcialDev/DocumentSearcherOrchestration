from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from config import settings
import os, time, threading

class SecretStore:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._init()
        return cls._instance

    def _init(self):
        self._kv_uri = settings.KV_URL
        self._cred = DefaultAzureCredential()
        self._client = SecretClient(vault_url=self._kv_uri, credential=self._cred)
        self._cache = {}  # name -> {"v": value, "t": timestamp}
        self._ttl = int(os.getenv("SECRETS_TTL_SECONDS", "1800"))
        self._cache_lock = threading.Lock()

    def get(self, name: str) -> str:
        now = time.time()
        # fetch from cache
        with self._cache_lock:
            item = self._cache.get(name)
            if item and (now - item["t"] < self._ttl):
                return item["v"]

        # fetch latest from Key Vault if TTL expired
        val = self._client.get_secret(name).value
        with self._cache_lock:
            self._cache[name] = {"v": val, "t": now}
        return val

def get_secret(name: str) -> str:
    return SecretStore().get(name)