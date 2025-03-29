import os
import re
import sys

print("\n" + "=" * 60)
print("AAROHI VERIFICATION TOOL")
print("=" * 60)
print("\nChecking bot code for channel restriction...\n")

BOT_FILE = "standalone_bot.py"

if not os.path.exists(BOT_FILE):
    print(f"❌ Error: {BOT_FILE} not found!")
    sys.exit(1)

try:
    with open(BOT_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Check for global constant
    if not re.search(r'ALLOWED_CHANNEL_ID\s*=\s*1353429400460198032', content):
        print("❌ Error: ALLOWED_CHANNEL_ID global constant not found or incorrect!")
    else:
        print("✅ ALLOWED_CHANNEL_ID global constant found.")
    
    # Check for on_message handler with channel restriction
    if not re.search(r'if\s+message\.channel\.id\s*!=\s*ALLOWED_CHANNEL_ID', content):
        print("❌ Error: Channel ID check in on_message handler not found!")
    else:
        print("✅ Channel restriction in on_message handler found.")
    
    # Check for early return
    if not re.search(r'if\s+message\.channel\.id\s*!=\s*ALLOWED_CHANNEL_ID.*?return', content, re.DOTALL):
        print("❌ Error: Early return after channel check not found!")
    else:
        print("✅ Early return after channel check found.")
    
    print("\nVerification complete!")
    
    if all([
        re.search(r'ALLOWED_CHANNEL_ID\s*=\s*1353429400460198032', content),
        re.search(r'if\s+message\.channel\.id\s*!=\s*ALLOWED_CHANNEL_ID', content),
        re.search(r'if\s+message\.channel\.id\s*!=\s*ALLOWED_CHANNEL_ID.*?return', content, re.DOTALL)
    ]):
        print("\n✅ All channel restriction checks passed! Your bot should only respond in the specified channel.")
    else:
        print("\n⚠️ Some checks failed. The bot may not be properly restricted to the specified channel.")
    
except Exception as e:
    print(f"❌ Error while verifying bot code: {e}")

print("\nPress Enter to exit...")
input() 