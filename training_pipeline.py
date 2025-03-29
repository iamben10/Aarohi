import json
import os
import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import re
from pathlib import Path
import time
import asyncio
import threading

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('training_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TrainingPipeline:
    def __init__(self, db_path: str = 'aarohi_brain.db'):
        """Initialize the training pipeline with database connection"""
        self.db_path = db_path
        self.setup_database()
        self.running = False
        self.monitor_thread = None
        logger.info("Training pipeline initialized")

    def setup_database(self):
        """Create SQLite database and tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create training pairs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS training_pairs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                input_text TEXT NOT NULL,
                output_text TEXT NOT NULL,
                emotion_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                source TEXT,
                confidence FLOAT DEFAULT 1.0
            )
        ''')
        
        # Create emotion patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emotion_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern TEXT NOT NULL,
                emotion_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database setup completed")

    def ingest_chat_file(self, file_path: str, source: str = "instagram"):
        """Process and store chat data from a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for message in data:
                # Clean and preprocess the message
                cleaned_input = self._clean_text(message.get('input', ''))
                cleaned_output = self._clean_text(message.get('output', ''))
                
                if cleaned_input and cleaned_output:
                    cursor.execute('''
                        INSERT INTO training_pairs (input_text, output_text, source)
                        VALUES (?, ?, ?)
                    ''', (cleaned_input, cleaned_output, source))
            
            conn.commit()
            conn.close()
            logger.info(f"Successfully ingested chat file: {file_path}")
            
        except Exception as e:
            logger.error(f"Error ingesting chat file {file_path}: {str(e)}")
            raise

    def _clean_text(self, text: str) -> str:
        """Clean and preprocess text by removing excess emojis and metadata"""
        # Remove emojis
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emojis
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE)
        
        text = emoji_pattern.sub(r'', text)
        
        # Remove timestamps and other metadata
        text = re.sub(r'\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?', '', text)
        
        # Clean up whitespace
        text = ' '.join(text.split())
        
        return text.strip()

    def add_training_pair(self, input_text: str, output_text: str, emotion_type: Optional[str] = None):
        """Add a new training pair through interactive teaching"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO training_pairs (input_text, output_text, emotion_type)
                VALUES (?, ?, ?)
            ''', (input_text, output_text, emotion_type))
            
            conn.commit()
            conn.close()
            logger.info(f"Added new training pair: {input_text[:50]}...")
            
        except Exception as e:
            logger.error(f"Error adding training pair: {str(e)}")
            raise

    def find_response(self, user_input: str) -> Tuple[str, float]:
        """Find the best matching response for user input"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all training pairs
            cursor.execute('SELECT input_text, output_text, confidence FROM training_pairs')
            pairs = cursor.fetchall()
            
            best_match = None
            best_confidence = 0.0
            
            for pair in pairs:
                input_text, output_text, confidence = pair
                # Simple similarity check (can be improved with better matching algorithms)
                similarity = self._calculate_similarity(user_input.lower(), input_text.lower())
                if similarity > best_confidence:
                    best_confidence = similarity
                    best_match = output_text
            
            conn.close()
            
            if best_match and best_confidence > 0.5:  # Confidence threshold
                return best_match, best_confidence
            else:
                return "I'm still learning. Could you teach me how to respond to that?", 0.0
                
        except Exception as e:
            logger.error(f"Error finding response: {str(e)}")
            return "I encountered an error while processing your message.", 0.0

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts (simple implementation)"""
        # Split into words
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0

    async def monitor_chat_folder_async(self, folder_path: str):
        """Asynchronously monitor a folder for new chat export files"""
        self.running = True
        folder = Path(folder_path)
        
        # Create folder if it doesn't exist
        if not folder.exists():
            folder.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created chat exports folder: {folder_path}")
            
        processed_files = set()
        
        while self.running:
            try:
                # Check for new files
                for file_path in folder.glob('*.json'):
                    if str(file_path) not in processed_files:
                        self.ingest_chat_file(str(file_path))
                        processed_files.add(str(file_path))
                
                # Use asyncio.sleep instead of time.sleep to prevent blocking
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error monitoring folder: {str(e)}")
                await asyncio.sleep(5)  # Wait longer on error
                
    def monitor_chat_folder(self, folder_path: str):
        """Non-blocking wrapper for monitor_chat_folder_async using threading"""
        def run_in_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.monitor_chat_folder_async(folder_path))
            loop.close()
        
        # Start monitoring in a separate thread
        self.monitor_thread = threading.Thread(target=run_in_thread, daemon=True)
        self.monitor_thread.start()
        return self.monitor_thread
        
    def stop_monitoring(self):
        """Stop the monitoring process"""
        self.running = False
        logger.info("Chat folder monitoring stopped")

    def get_training_stats(self) -> Dict:
        """Get statistics about the training data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM training_pairs')
            total_pairs = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(DISTINCT emotion_type) FROM training_pairs WHERE emotion_type IS NOT NULL')
            emotion_types = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "total_training_pairs": total_pairs,
                "emotion_types_covered": emotion_types,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting training stats: {str(e)}")
            return {"error": str(e)} 
