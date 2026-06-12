#!/usr/bin/env python3
"""
ChatterMate - Model Preloader
Copyright (C) 2024 ChatterMate

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>
"""

import os
import sys
import logging
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, '/app')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def preload_sentence_transformer():
    """Preload the sentence transformer model to avoid runtime issues"""
    try:
        from sentence_transformers import SentenceTransformer
        
        # Get model ID from environment or use default
        model_id = os.getenv("EMBEDDING_MODEL_ID", "sentence-transformers/all-MiniLM-L6-v2")
        
        logger.info(f"Preloading SentenceTransformer model: {model_id}")
        
        # Load the model (this will download it if not cached)
        model = SentenceTransformer(model_id)
        
        # Test the model with a simple embedding to ensure it's working
        test_text = "This is a test sentence to verify the model is working correctly."
        embedding = model.encode(test_text)
        
        logger.info(f"Successfully preloaded model {model_id}. Embedding dimension: {len(embedding)}")
        
        # Clean up to free memory
        del model
        del embedding
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to preload SentenceTransformer model: {str(e)}")
        return False

def preload_agno_embedder():
    """Preload the Agno embedder to ensure it's working"""
    try:
        from agno.embedder.fastembed import FastEmbedEmbedder
        
        # Get model ID from environment or use default
        model_id = os.getenv("FASTEMBED_MODEL", "BAAI/bge-small-en-v1.5")
        
        logger.info(f"Preloading Agno FastEmbedEmbedder: {model_id}")
        
        # Initialize the embedder
        embedder = FastEmbedEmbedder(id=model_id)
        
        # Test embedding using the correct API method
        test_text = "Test embedding for Agno embedder initialization."
        embedding = embedder.get_embedding(test_text)
        
        logger.info(f"Successfully preloaded Agno embedder {model_id}. Embedding dimension: {len(embedding)}")
        
        # Clean up
        del embedder
        del embedding
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to preload Agno embedder: {str(e)}")
        return False

def main():
    """Main function to preload all models"""
    # Check if we are using external models
    embedding_provider = os.getenv("EMBEDDING_PROVIDER", "fastembed")
    if embedding_provider.lower() in ("openai", "google", "gemini", "external"):
        logger.info(f"Skipping model preloading because EMBEDDING_PROVIDER={embedding_provider} uses external API models.")
        return 0

    logger.info("Starting model preloading process...")
    
    success = True
    
    # Preload SentenceTransformer model
    if not preload_sentence_transformer():
        success = False
    
    # Preload Agno embedder
    if not preload_agno_embedder():
        success = False
    
    if success:
        logger.info("All models preloaded successfully!")
        return 0
    else:
        logger.error("Some models failed to preload")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 