import base64

# Base64-encoded string
encoded_str = "   "

# Decode the Base64 string
decoded_bytes = base64.b64decode(encoded_str)

# Convert bytes to string (assuming UTF-8 encoding)
decoded_str = decoded_bytes.decode('utf-8')

print("Decoded string:", decoded_str)
