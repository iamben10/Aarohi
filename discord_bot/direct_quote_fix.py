import re
import os
import shutil

# Path to the productivity.py file
productivity_path = os.path.join("cogs", "productivity.py")

# Create a backup first
backup_path = productivity_path + ".quote_fix_backup"
try:
    shutil.copy2(productivity_path, backup_path)
    print(f"✅ Created backup at {backup_path}")
except Exception as e:
    print(f"❌ Error creating backup: {e}")

# Read the file content
try:
    with open(productivity_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    print("✅ Successfully read the productivity.py file")
except Exception as e:
    try:
        with open(productivity_path, 'r', encoding='latin-1', errors='ignore') as f:
            content = f.read()
        print(f"✅ Read file with latin-1 encoding: {e}")
    except Exception as e2:
        print(f"❌ Failed to read file: {e2}")
        exit(1)

# Find the quote command section
quote_pattern = re.compile(r'(@commands\.command\(name="quote"\).*?async\s+def\s+quote\(self,\s+ctx.*?\).*?)(?=\s*@commands|\s*async\s+def|\s*def|\Z)', re.DOTALL)
match = quote_pattern.search(content)

if match:
    print("✅ Found the quote command section")
    old_code = match.group(1)
    
    # For debugging - print the first 200 chars of the old code
    print(f"\nOld code snippet (first 200 chars):\n{old_code[:200]}...\n")
    
    # The new implementation - consolidates all messages into a single embed
    new_code = '''@commands.command(name="quote")
    async def quote(self, ctx, category: Optional[str] = None):
        """Get an inspirational quote"""
        # Dictionary of quotes by category
        quotes = {
            "motivation": [
                ("Believe you can and you're halfway there.", "Theodore Roosevelt"),
                ("You are never too old to set another goal or to dream a new dream.", "C.S. Lewis"),
                ("Don't watch the clock; do what it does. Keep going.", "Sam Levenson"),
                ("The future belongs to those who believe in the beauty of their dreams.", "Eleanor Roosevelt"),
                ("It always seems impossible until it's done.", "Nelson Mandela")
            ],
            "success": [
                ("Success is not final, failure is not fatal: It is the courage to continue that counts.", "Winston Churchill"),
                ("The road to success and the road to failure are almost exactly the same.", "Colin R. Davis"),
                ("Success usually comes to those who are too busy to be looking for it.", "Henry David Thoreau"),
                ("The secret of success is to do the common thing uncommonly well.", "John D. Rockefeller Jr."),
                ("I find that the harder I work, the more luck I seem to have.", "Thomas Jefferson")
            ],
            "focus": [
                ("Concentrate all your thoughts upon the work in hand.", "Alexander Graham Bell"),
                ("The successful warrior is the average man, with laser-like focus.", "Bruce Lee"),
                ("My success, part of it certainly, is that I have focused in on a few things.", "Bill Gates"),
                ("That's been one of my mantras - focus and simplicity.", "Steve Jobs"),
                ("The main thing is to keep the main thing the main thing.", "Stephen Covey")
            ]
        }
        
        # All quotes together for random selection
        all_quotes = []
        for category_quotes in quotes.values():
            all_quotes.extend(category_quotes)
            
        # Determine which quote to show
        if category and category.lower() in quotes:
            # Get a quote from the specific category
            quote_text, author = random.choice(quotes[category.lower()])
            cat_display = category.capitalize()
        else:
            # Get a random quote from any category
            quote_text, author = random.choice(all_quotes)
            cat_display = "Inspirational"
            
        # Create embed for the quote
        embed = discord.Embed(
            title=f"{cat_display} Quote",
            description=f"**\"{quote_text}\"**",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"— {author}")
        
        # Add available categories to the embed if no category was specified or an invalid one was given
        if not category or (category and category.lower() not in quotes):
            categories = ", ".join([f"`{cat}`" for cat in quotes.keys()])
            embed.add_field(name="Available Categories", value=f"Try: {categories}")
            
        # Send a single consolidated response
        await ctx.send(embed=embed)'''
    
    # Replace the old implementation with the new one
    new_content = content.replace(old_code, new_code)
    
    # Save the modified file
    try:
        with open(productivity_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("✅ Successfully updated the quote command!")
        print("\n🎉 The quote command now sends only ONE message with everything consolidated.")
        print("   Just run your bot normally - no need for separate batch files.")
    except Exception as e:
        print(f"❌ Error saving the modified file: {e}")
        print("   The original file is unchanged.")
else:
    print("❌ Could not find the quote command in the file.")
    print("   Please check if the productivity.py file contains the quote command.") 