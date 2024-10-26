import time
import random

def uuid():
    # Get the current timestamp in base 36
    timestamp = base36encode(int(time.time() * 1000))
    
    # Generate a random segment in base 36
    random_segment = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=12))
    
    # Combine both parts to get a simple UUID
    return f"{timestamp}-{random_segment}"

def base36encode(number):
    """Convert an integer to a base36 string."""
    alphabet = '0123456789abcdefghijklmnopqrstuvwxyz'
    base36 = ''
    while number:
        number, i = divmod(number, 36)
        base36 = alphabet[i] + base36
    return base36 or alphabet[0]
