from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
from typing import Any


BLOCKED_OPERATIONS = [
    "password guessing/cracking",
    "handshake/PMKID capture",
    "WPS PIN attacks",
    "deauthentication",
    "packet injection",
    "permission/root bypass",
