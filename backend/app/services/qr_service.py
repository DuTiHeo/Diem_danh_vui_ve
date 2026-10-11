import random
import hashlib
from datetime import datetime, timedelta
from typing import Tuple

def generate_pin_and_hash() -> Tuple[str, str]:
    """
    Generates a 6-digit PIN and its SHA256 hash.
    PIN is used for public display and input.
    Hash is used internally to verify (though PIN is unique in the table, 
    hash is added security for the QR embedded link).
    """
    # Generate 6-digit PIN
    pin_code = str(random.randint(100000, 999999))
    
    # Generate hash
    token_hash = hashlib.sha256(pin_code.encode()).hexdigest()
    
    return pin_code, token_hash

def get_expiration_time(seconds: int = 60) -> datetime:
    """
    Returns the expiration datetime, default 60 seconds from now.
    """
    return datetime.utcnow() + timedelta(seconds=seconds)

