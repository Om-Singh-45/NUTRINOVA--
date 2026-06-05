# NutriNova AI: Intelligent Food Analysis & Personalized Nutrition System

NutriNova AI is an advanced, end-to-end web platform designed to analyze dietary choices and offer highly personalized nutrition and wellness advice. Using computer vision for food item identification, database indexing for nutritional details, and Retrieval-Augmented Generation (RAG) for conversational health intelligence, NutriNova AI serves as a comprehensive digital nutritionist.

This project was built as a **Major Academic Project** demonstrating the integration of Deep Learning, Natural Language Processing, and web technologies.

---

## 📸 System Overview & UI Design
NutriNova AI features a modern dashboard equipped with:
*   **Deep-Learning Food Classifier**: Accepts local file uploads or image URLs to identify food categories.
*   **Interactive Calorie Tracker**: Uses user biometric details to calculate custom calorie limits and visualizes consumption progress in real-time.
*   **RAG-Enhanced Health Chatbot**: An expert assistant grounded in verified nutrition facts, implementing automated safety mechanisms and medical search filters.

---

## 🏗️ System Architecture

The following diagram illustrates the workflow and data transitions of NutriNova AI:

```mermaid
graph TD
    User([User / Browser])
    Flask[Flask Backend Server: app.py]
    DB[(SQLite DB: nutrition_app.db)]
    HF[Hugging Face: Mullerjo/food-101-finetuned-model]
    USDA[USDA FoodData Central API]
    Gemini[Gemini 2.5 Flash API]
    RAG[Health RAG System: rag_system.py]
    KB[(Knowledge Base: .txt documents)]
    FAISS[(FAISS Vector Database)]

    User <-->|HTTP / HTML / JS| Flask
    Flask <-->|Read / Write Profiles & Logs| DB
    Flask -->|Run Classification Model| HF
    Flask -->|Query Food Nutrients| USDA
    Flask -->|Personalized Prompts & Context| Gemini
    Flask <-->|Context Retrieval & Filters| RAG
    RAG <-->|Load & Chunk Texts| KB
    RAG <-->|Serialize & Retrieve Embeddings| FAISS
