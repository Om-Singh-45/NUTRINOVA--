"""
RAG (Retrieval-Augmented Generation) System for Health Chatbot
================================================================

This module implements a RAG pipeline to prevent hallucinations and ensure
accurate health advice based on verified knowledge base documents.

Features:
- Automatic embedding generation from .txt files
- FAISS vector database for fast similarity search
- Sentence transformers for semantic search
- Auto-reload when new files are added to knowledge base
- Medical question safety filter

Author: Health Chatbot System
"""

import os
import pickle
from typing import List, Dict, Tuple
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss


class HealthRAGSystem:
    """
    RAG System for health and nutrition chatbot.
    
    This class handles:
    1. Loading and chunking knowledge base documents
    2. Creating and storing embeddings
    3. Retrieving relevant context for user queries
    4. Safety filtering for medical questions
    """
    
    def __init__(
        self,
        knowledge_base_dir: str = "nutrition_knowledge",
        embedding_model: str = "all-MiniLM-L6-v2",
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ):
        """
        Initialize the RAG system.
        
        Args:
            knowledge_base_dir: Directory containing .txt knowledge files
            embedding_model: SentenceTransformer model to use
            chunk_size: Size of text chunks (characters)
            chunk_overlap: Overlap between chunks (characters)
        """
        self.knowledge_base_dir = Path(knowledge_base_dir)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Create knowledge base directory if it doesn't exist
        self.knowledge_base_dir.mkdir(exist_ok=True)
        
        # Initialize embedding model
        print("Loading embedding model...")
        self.embedding_model = SentenceTransformer(embedding_model)
        print("✓ Embedding model loaded successfully!")
        
        # Storage for documents and embeddings
        self.documents: List[Dict[str, str]] = []
        self.embeddings: np.ndarray | None = None
        self.index: faiss.IndexFlatL2 | None = None
        
        # Cache file paths
        self.cache_dir = Path("rag_cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.embeddings_cache = self.cache_dir / "embeddings.pkl"
        self.docs_cache = self.cache_dir / "documents.pkl"
        
        # Medical/diagnostic keywords to filter
        self.medical_keywords = [
            "diagnose", "diagnosis", "disease", "medicine", "medication",
            "prescription", "drug", "cure", "treatment", "therapy",
            "symptoms", "illness", "sick", "cancer", "diabetes",
            "blood pressure", "heart attack", "stroke", "infection",
            "doctor", "hospital", "medical", "clinical"
        ]
        
        # Health/nutrition related keywords (in-scope topics)
        # Using word stems to catch variations (e.g., hydrat catches hydrated, hydration, hydrate)
        self.nutrition_keywords = [
            "diet", "nutrition", "food", "eat", "meal", "calorie", "weight",
            "protein", "carb", "fat", "fiber", "fibre", "vitamin", "mineral",
            "healthy", "health", "water", "hydrat", "drink", "fluid",
            "breakfast", "lunch", "dinner", "snack", "vegetable", "fruit",
            "exercise", "fitness", "balance", "energy", "supplement",
            "loss", "gain", "muscle", "junk", "fast food", "organic",
            "nutrient", "digest", "metabol", "immune", "wellness",
            "portion", "serving", "intake", "consume", "hunger", "appetite",
            "sugar", "sodium", "salt", "cholesterol", "grain", "dairy",
            "vegan", "vegetarian", "gluten", "allerg", "fresh", "natural",
            # Weight management specific
            "gain weight", "lose weight", "weight loss", "weight gain",
            "build muscle", "bulk", "bulking", "cutting", "lean", "tone"
        ]
        
        # Load or build the knowledge base
        self._initialize_knowledge_base()
    
    def _initialize_knowledge_base(self):
        """Load existing embeddings or create new ones from documents."""
        # Check if we need to rebuild
        if self._should_rebuild_index():
            print("Building knowledge base from documents...")
            self._build_knowledge_base()
        else:
            print("Loading cached knowledge base...")
            self._load_cache()
        
        print(f"✓ Knowledge base ready with {len(self.documents)} chunks!")
    
    def _should_rebuild_index(self) -> bool:
        """Check if we need to rebuild the index."""
        # Rebuild if cache doesn't exist
        if not self.embeddings_cache.exists() or not self.docs_cache.exists():
            return True
        
        # Rebuild if new files were added
        cache_time = self.embeddings_cache.stat().st_mtime
        for txt_file in self.knowledge_base_dir.glob("*.txt"):
            if txt_file.stat().st_mtime > cache_time:
                print(f"Detected new/updated file: {txt_file.name}")
                return True
        
        return False
    
    def _chunk_text(self, text: str, filename: str) -> List[Dict[str, str]]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: Full text to chunk
            filename: Source filename for reference
            
        Returns:
            List of dictionaries with 'text', 'source', and 'chunk_id'
        """
        chunks = []
        start = 0
        chunk_id = 0
        
        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end]
            
            # Try to end at a sentence boundary
            if end < len(text):
                last_period = chunk_text.rfind('.')
                last_newline = chunk_text.rfind('\n')
                boundary = max(last_period, last_newline)
                
                if boundary > self.chunk_size * 0.6:  # At least 60% of chunk
                    end = start + boundary + 1
                    chunk_text = text[start:end]
            
            chunks.append({
                'text': chunk_text.strip(),
                'source': filename,
                'chunk_id': chunk_id
            })
            
            chunk_id += 1
            start = end - self.chunk_overlap
        
        return chunks
    
    def _load_documents(self) -> List[Dict[str, str]]:
        """
        Load all .txt files from knowledge base directory.
        
        Returns:
            List of document chunks with metadata
        """
        all_chunks = []
        txt_files = list(self.knowledge_base_dir.glob("*.txt"))
        
        if not txt_files:
            print("⚠️  Warning: No .txt files found in knowledge base!")
            return []
        
        print(f"Loading {len(txt_files)} document(s)...")
        
        for txt_file in txt_files:
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    text = f.read()
                
                chunks = self._chunk_text(text, txt_file.name)
                all_chunks.extend(chunks)
                print(f"  ✓ {txt_file.name}: {len(chunks)} chunks")
                
            except Exception as e:
                print(f"  ✗ Error loading {txt_file.name}: {e}")
        
        return all_chunks
    
    def _build_knowledge_base(self):
        """Build embeddings and FAISS index from documents."""
        # Load documents
        self.documents = self._load_documents()
        
        if not self.documents:
            print("⚠️  No documents to index!")
            return
        
        # Create embeddings
        print("Creating embeddings...")
        texts = [doc['text'] for doc in self.documents]
        self.embeddings = self.embedding_model.encode(  # type: ignore[assignment]
            texts,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        # Build FAISS index
        print("Building FAISS index...")
        dimension = self.embeddings.shape[1]  # type: ignore[union-attr]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(self.embeddings)  # type: ignore[arg-type]
        
        # Save cache
        self._save_cache()
        print("✓ Knowledge base built and cached!")
    
    def _save_cache(self):
        """Save embeddings and documents to cache."""
        with open(self.embeddings_cache, 'wb') as f:
            pickle.dump({
                'embeddings': self.embeddings,
                'index': faiss.serialize_index(self.index)
            }, f)
        
        with open(self.docs_cache, 'wb') as f:
            pickle.dump(self.documents, f)
    
    def _load_cache(self):
        """Load embeddings and documents from cache."""
        try:
            with open(self.embeddings_cache, 'rb') as f:
                cache_data = pickle.load(f)
                self.embeddings = cache_data['embeddings']
                self.index = faiss.deserialize_index(cache_data['index'])
            
            with open(self.docs_cache, 'rb') as f:
                self.documents = pickle.load(f)
                
        except Exception as e:
            print(f"Error loading cache: {e}")
            self._build_knowledge_base()
    
    def is_nutrition_related(self, query: str, has_food_context: bool = False) -> bool:
        """
        Check if query is related to nutrition/health topics.
        
        Args:
            query: User's question
            has_food_context: True if there's recently analyzed food context
            
        Returns:
            True if query contains nutrition-related keywords or is a follow-up
        """
        query_lower = query.lower()
        
        # If there's food context, be more lenient with follow-up questions
        if has_food_context:
            # Common follow-up patterns when food was just analyzed
            follow_up_patterns = [
                'good for me', 'bad for me', 'should i eat', 'can i eat',
                'is it good', 'is it bad', 'healthy', 'unhealthy',
                'worth it', 'okay', 'alright', 'fine',
                'how much', 'how many', 'portion', 'serving',
                'better', 'worse', 'alternative', 'instead',
                'yes', 'no', 'maybe', 'what about', 'how about'
            ]
            
            for pattern in follow_up_patterns:
                if pattern in query_lower:
                    return True
            
            # Very short questions with food context are likely follow-ups
            if len(query.split()) <= 4:
                return True
        
        # Immediately reject obviously unrelated topics
        unrelated_keywords = [
            'speed', 'distance', 'physics', 'formula', 'math', 'equation',
            'politics', 'election', 'president', 'government', 'congress',
            'technology', 'programming', 'computer', 'software', 'code',
            'weather', 'climate', 'temperature', 'rain', 'snow',
            'sports score', 'football match', 'basketball game', 'soccer score',
            'movie', 'film', 'actor', 'actress', 'cinema',
            'music album', 'song lyrics', 'concert', 'band',
            'history battle', 'war date', 'geography capital', 'country population',
            'chemistry element', 'astronomy planet', 'physics law'
        ]
        
        for keyword in unrelated_keywords:
            if keyword in query_lower:
                return False
        
        # Enhanced nutrition keywords - check for word stems too
        # Check multi-word phrases FIRST (more specific)
        for keyword in self.nutrition_keywords:
            if ' ' in keyword:  # Multi-word phrase
                if keyword in query_lower:
                    return True
        
        # Then check single words/stems
        for keyword in self.nutrition_keywords:
            if ' ' not in keyword:  # Single word/stem
                if keyword in query_lower:
                    return True
        
        # Check for common question patterns about health/nutrition
        health_patterns = [
            'what should i eat', 'what to eat', 'how to eat',
            'what should i drink', 'what to drink', 'how to drink',
            'stay fit', 'get fit', 'lose weight', 'gain weight',
            'build muscle', 'burn fat', 'how many calories',
            'is it healthy', 'is this healthy', 'good for health',
            'bad for health', 'nutritious', 'nutrient',
            'wellness', 'wellbeing', 'stay healthy',
            'eat better', 'eating habit', 'dietary', 'diet plan',
            'meal plan', 'food choice', 'healthy lifestyle',
            'balanced diet', 'nutrition tip', 'health tip',
            # Weight specific patterns
            'how to gain', 'how to lose', 'ways to gain', 'ways to lose',
            'tips for weight', 'help me gain', 'help me lose'
        ]
        
        for pattern in health_patterns:
            if pattern in query_lower:
                return True
        
        # If query mentions common health/wellness verbs with body/health context
        health_verbs = ['maintain', 'improve', 'boost', 'increase', 'decrease', 'reduce', 'manage']
        health_nouns = ['body', 'health', 'wellness', 'fitness', 'immunity', 'metabolism', 'digestion']
        
        has_health_verb = any(verb in query_lower for verb in health_verbs)
        has_health_noun = any(noun in query_lower for noun in health_nouns)
        
        if has_health_verb and has_health_noun:
            return True
        
        # Default: If nothing matched, reject
        return False
    
    def is_medical_question(self, query: str) -> bool:
        """
        Check if query is asking for medical diagnosis or treatment.
        
        Args:
            query: User's question
            
        Returns:
            True if query contains medical/diagnostic keywords
        """
        query_lower = query.lower()
        
        for keyword in self.medical_keywords:
            if keyword in query_lower:
                return True
        
        return False
    
    def retrieve_context(
        self,
        query: str,
        top_k: int = 3,
        similarity_threshold: float = 1.5
    ) -> List[Dict[str, str]]:
        """
        Retrieve most relevant documents for a query.
        
        Args:
            query: User's question
            top_k: Number of top documents to retrieve
            similarity_threshold: Maximum distance for relevance (lower = more similar)
            
        Returns:
            List of relevant document chunks with metadata
        """
        if not self.documents or self.index is None:
            print("⚠️  Knowledge base is empty!")
            return []
        
        # Create query embedding
        query_embedding = self.embedding_model.encode(
            [query],
            convert_to_numpy=True
        )
        
        # Search FAISS index
        distances, indices = self.index.search(query_embedding, top_k)  # type: ignore[call-arg]
        
        # Filter by similarity threshold and prepare results
        relevant_docs = []
        for dist, idx in zip(distances[0], indices[0]):
            if dist <= similarity_threshold:
                doc = self.documents[idx].copy()
                doc['similarity_score'] = float(dist)
                relevant_docs.append(doc)
        
        return relevant_docs
    
    def format_context_for_llm(self, retrieved_docs: List[Dict[str, str]]) -> str:
        """
        Format retrieved documents into context string for LLM.
        
        Args:
            retrieved_docs: List of retrieved document chunks
            
        Returns:
            Formatted context string
        """
        if not retrieved_docs:
            return "No specific information found in knowledge base."
        
        context_parts = []
        for i, doc in enumerate(retrieved_docs, 1):
            context_parts.append(
                f"[Source {i}: {doc['source']}]\n{doc['text']}\n"
            )
        
        return "\n---\n".join(context_parts)
    
    def reload_knowledge_base(self):
        """
        Manually reload knowledge base (useful after adding new files).
        Call this to refresh the index without restarting the application.
        """
        print("Reloading knowledge base...")
        self._build_knowledge_base()
    
    def get_rag_response_context(
        self,
        user_query: str,
        top_k: int = 3,
        has_food_context: bool = False
    ) -> Tuple[str, bool]:
        """
        Main method to get context for user query with safety check.
        
        Args:
            user_query: User's question
            top_k: Number of documents to retrieve
            has_food_context: True if there's recently analyzed food
            
        Returns:
            Tuple of (formatted_context, is_safe_question)
        """
        # Safety check for medical questions
        if self.is_medical_question(user_query):
            return (
                "⚠️ I cannot provide medical diagnoses or treatment advice. "
                "Please consult a qualified healthcare professional for medical concerns.",
                False
            )
        
        # Check if question is nutrition-related (considering food context)
        if not self.is_nutrition_related(user_query, has_food_context=has_food_context):
            return (
                "I can only answer questions about nutrition, diet, healthy eating, weight management, "
                "hydration, and general wellness. Please ask a question related to these topics.",
                False
            )
        
        # Retrieve relevant context
        relevant_docs = self.retrieve_context(user_query, top_k=top_k)
        
        # If no relevant documents found, return message
        if not relevant_docs:
            return (
                "I don't have specific information about that in my knowledge base. "
                "I can help you with questions about balanced diet, weight loss, hydration, "
                "post-junk food recovery, and general nutrition advice.",
                True  # Still safe, just no context
            )
        
        # Format for LLM
        context = self.format_context_for_llm(relevant_docs)
        
        return context, True


# ============================================
# CONVENIENCE FUNCTIONS
# ============================================

def create_rag_system() -> HealthRAGSystem:
    """
    Factory function to create and initialize RAG system.
    
    Returns:
        Initialized HealthRAGSystem instance
    """
    return HealthRAGSystem(
        knowledge_base_dir="nutrition_knowledge",
        embedding_model="all-MiniLM-L6-v2",
        chunk_size=500,
        chunk_overlap=50
    )


# ============================================
# EXAMPLE USAGE (for testing)
# ============================================

if __name__ == "__main__":
    print("="*60)
    print("Testing RAG System")
    print("="*60)
    
    # Initialize RAG system
    rag = create_rag_system()
    
    # Test queries
    test_queries = [
        "I ate a lot of fries today. How do I balance my diet tomorrow?",
        "What should I eat for weight loss?",
        "How much water should I drink daily?",
        "Do I have diabetes?",  # Medical question - should be blocked
    ]
    
    print("\n" + "="*60)
    print("Testing Queries")
    print("="*60)
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        print("-" * 60)
        
        context, is_safe = rag.get_rag_response_context(query, top_k=2)
        
        if not is_safe:
            print(f"🚫 BLOCKED: {context}")
        else:
            print("✅ Retrieved Context:")
            print(context[:500] + "..." if len(context) > 500 else context)
        
        print()
