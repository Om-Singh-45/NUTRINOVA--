from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from transformers import AutoImageProcessor, AutoModelForImageClassification
from PIL import Image
import torch
import requests
import json
from typing import Dict, Any
from rag_system import create_rag_system
import secrets
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import functools

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # For session management

# --------------------------------------------------------------
# Database Setup
# --------------------------------------------------------------
DATABASE = 'nutrition_app.db'

def get_db():
    """Get database connection."""
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    """Initialize database tables."""
    db = get_db()
    cursor = db.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # User profile table for health metrics
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            age INTEGER,
            gender TEXT,
            height REAL,
            weight REAL,
            target_weight REAL,
            activity_level TEXT,
            goal TEXT,
            dietary_restrictions TEXT,
            health_conditions TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Food analysis history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS food_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            food_name TEXT NOT NULL,
            confidence REAL,
            calories TEXT,
            protein TEXT,
            fat TEXT,
            carbohydrates TEXT,
            fiber TEXT,
            sugar TEXT,
            sodium TEXT,
            cholesterol TEXT,
            dietary_advice TEXT,
            image_url TEXT,
            analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Daily calorie tracking table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_calorie_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            log_date DATE NOT NULL,
            target_calories REAL,
            actual_calories REAL DEFAULT 0,
            foods_eaten TEXT,  -- JSON array of food names
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, log_date),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    db.commit()
    db.close()
    print("✓ Database initialized successfully!")

# Initialize database on startup
init_db()

def login_required(f):
    """Decorator to require login for routes."""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Please log in to access this feature"}), 401
        return f(*args, **kwargs)
    return decorated_function


def calculate_daily_calorie_target(user_profile):
    """
    Calculate daily calorie target based on user profile using Mifflin-St Jeor Equation.
    
    Args:
        user_profile: Dictionary with age, gender, weight, height, activity_level, goal
    
    Returns:
        Target calories per day (integer)
    """
    try:
        age = int(user_profile['age'])
        gender = user_profile['gender']
        weight = float(user_profile['weight'])  # kg
        height = float(user_profile['height'])  # cm
        activity_level = user_profile['activity_level']
        goal = user_profile['goal']
        
        # Mifflin-St Jeor Equation for BMR
        if gender == 'male':
            bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
        else:  # female or other
            bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
        
        # Activity multipliers
        activity_multipliers = {
            'sedentary': 1.2,
            'light': 1.375,
            'moderate': 1.55,
            'active': 1.725,
            'extra-active': 1.9
        }
        
        activity_multiplier = activity_multipliers.get(activity_level, 1.55)
        tdee = bmr * activity_multiplier  # Total Daily Energy Expenditure
        
        # Adjust based on goal
        if goal == 'lose-weight':
            # Deficit of 500 calories/day = ~0.5kg/week loss
            target = tdee - 500
        elif goal == 'gain-weight':
            # Surplus of 500 calories/day = ~0.5kg/week gain
            target = tdee + 500
        elif goal == 'build-muscle':
            # Moderate surplus for muscle gain
            target = tdee + 300
        else:  # maintain-weight or improve-health
            target = tdee
        
        # Ensure minimum safe calories
        min_calories = 1200 if gender == 'female' else 1500
        target = max(target, min_calories)
        
        return int(round(target))
        
    except Exception as e:
        print(f"Calorie calculation error: {e}")
        return 2000  # Default fallback

# --------------------------------------------------------------
# 1. Load pretrained food recognition model (from Hugging Face)
# --------------------------------------------------------------
MODEL_NAME = "Mullerjo/food-101-finetuned-model"
processor = AutoImageProcessor.from_pretrained(MODEL_NAME)
model = AutoModelForImageClassification.from_pretrained(MODEL_NAME)

# --------------------------------------------------------------
# 2. USDA FoodData Central API Key
# --------------------------------------------------------------
USDA_API_KEY = "3Kgatf87doj505tQrlmooX2TDgpDij3fr8ZaBZLc"

# --------------------------------------------------------------
# 3. Gemini API Key
# --------------------------------------------------------------
GEMINI_API_KEY = "AIzaSyBkbn4Cdk4CnhFlrPfe3gsOWlNZaiVgGPo"
# Use gemini-2.5-flash which is a stable, production-ready model
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

# --------------------------------------------------------------
# 4. Initialize RAG System for Health Chatbot
# --------------------------------------------------------------
print("\n" + "="*60)
print("Initializing RAG System for Health Chatbot...")
print("="*60)
rag_system = create_rag_system()
print("✓ RAG System initialized and ready!")
print("="*60 + "\n")

# --------------------------------------------------------------
# Helper function
# --------------------------------------------------------------
def _extract_name_value_unit(n):
    name, value, unit = "", None, None
    if isinstance(n, dict):
        if "nutrient" in n and isinstance(n["nutrient"], dict):
            name = n["nutrient"].get("name", "") or ""
            unit = n["nutrient"].get("unitName") or n.get("unitName")
            value = n.get("amount", n.get("value"))
        else:
            name = n.get("nutrientName", "") or n.get("name", "")
            unit = n.get("unitName") or n.get("unit")
            value = n.get("value", n.get("amount"))
    name = (name or "").strip().lower()
    if unit:
        unit = str(unit).strip().upper()
    return name, value, unit


def get_llm_dietary_advice(food_name, nutrients, confidence, user_profile=None):
    """
    Call Gemini API to get dietary advice and portion analysis
    Optionally includes user profile for personalized recommendations
    """
    try:
        # Prepare nutrition info for LLM
        nutrition_text = ", ".join([
            f"{k}: {v}" for k, v in nutrients.items() if v != "N/A"
        ])
        
        # Add user context if available
        user_context = ""
        if user_profile:
            # Calculate BMI
            height_m = user_profile['height'] / 100
            bmi = user_profile['weight'] / (height_m * height_m) if height_m > 0 else 0
            
            user_context = f"""

USER PROFILE (Use this to personalize your advice):
- Age: {user_profile['age']} years
- Gender: {user_profile['gender']}
- Height: {user_profile['height']} cm
- Weight: {user_profile['weight']} kg
- BMI: {bmi:.1f}
- Goal: {user_profile['goal']}
- Activity Level: {user_profile['activity_level']}
- Dietary Restrictions: {user_profile['dietary_restrictions'] if user_profile['dietary_restrictions'] else 'None'}
- Health Conditions: {user_profile['health_conditions'] if user_profile['health_conditions'] else 'None'}

IMPORTANT: Tailor your assessment based on their goal. For example:
- If goal is weight loss: Focus on calorie deficit, recommend smaller portions
- If goal is weight gain: Focus on calorie surplus, recommend larger portions or additions
- If goal is muscle building: Emphasize protein content
- Consider their dietary restrictions and health conditions"""
        
        prompt = f"""You are a professional nutritionist analyzing a food image. Provide a concise, structured response.{user_context}

Food Detected: {food_name}
Confidence: {confidence:.2f}%
Nutrition (per 100g): {nutrition_text}

Respond in this EXACT format with these 3 sections only:

**Food Name:** [Name of the analyzed food]

**Quantity:** [Estimated portion size in grams as seen in the image, e.g., "150g" or "~200g"]

**Weight Goal Assessment:**
- For Weight Loss: [Good/Moderate/Not Recommended] - [Brief reason considering user's profile]
- For Weight Gain: [Good/Moderate/Not Recommended] - [Brief reason considering user's profile]

Keep each section brief and practical. No additional sections or explanations."""

        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 800
            }
        }
        
        response = requests.post(
            f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if "candidates" in data and len(data["candidates"]) > 0 and "content" in data["candidates"][0] and "parts" in data["candidates"][0]["content"] and len(data["candidates"][0]["content"]["parts"]) > 0:
                advice = data["candidates"][0]["content"]["parts"][0]["text"]
                # Clean and format the response
                advice = format_llm_response(advice)
                return advice
            else:
                return "Unable to generate dietary advice at this time."
        else:
            print(f"LLM API error: {response.status_code} - {response.text}")
            return "Unable to generate dietary advice. Please try again."
            
    except Exception as e:
        print(f"LLM error: {e}")
        return "Dietary analysis temporarily unavailable."


def format_llm_response(raw_text):
    """
    Clean and format LLM response by removing markdown symbols
    """
    if not raw_text:
        return raw_text
    
    # Remove markdown bold markers
    text = raw_text.replace('**', '')
    # Remove extra asterisks
    text = text.replace('*', '')
    # Clean up extra whitespace
    text = '\n'.join(line.strip() for line in text.split('\n'))
    # Remove excessive newlines
    while '\n\n\n' in text:
        text = text.replace('\n\n\n', '\n\n')
    
    return text.strip()


@app.route("/chat", methods=["POST"])
def health_chat():
    """
    RAG-powered health expert chatbot endpoint.
    Uses retrieval-augmented generation to provide accurate,
    grounded responses based on verified knowledge base.
    Includes context from recently analyzed food and user profile if available.
    """
    try:
        # Try to get JSON data with force=True to handle escaping issues
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400
            
        user_message = data.get('message', '').strip()
        food_context = data.get('food_context')  # Optional: recent food analysis
        
        if not user_message:
            return jsonify({"error": "Please enter a message"}), 400
        
        # Get user profile if logged in
        user_profile = None
        calorie_context = None
        if 'user_id' in session:
            try:
                from datetime import date
                today = str(date.today())
                
                db = get_db()
                profile = db.execute(
                    'SELECT * FROM user_profiles WHERE user_id = ?',
                    (session['user_id'],)
                ).fetchone()
                
                if profile:
                    user_profile = {
                        'age': profile['age'],
                        'gender': profile['gender'],
                        'height': profile['height'],
                        'weight': profile['weight'],
                        'target_weight': profile['target_weight'],
                        'activity_level': profile['activity_level'],
                        'goal': profile['goal'],
                        'dietary_restrictions': profile['dietary_restrictions'],
                        'health_conditions': profile['health_conditions']
                    }
                    
                    # Get today's calorie data
                    calorie_log = db.execute(
                        'SELECT * FROM daily_calorie_log WHERE user_id = ? AND log_date = ?',
                        (session['user_id'], today)
                    ).fetchone()
                    
                    if calorie_log:
                        target_calories = calculate_daily_calorie_target(user_profile)
                        calorie_context = {
                            'target': target_calories,
                            'actual': calorie_log['actual_calories'],
                            'remaining': target_calories - calorie_log['actual_calories'],
                            'foods_count': len(json.loads(calorie_log['foods_eaten'])) if calorie_log['foods_eaten'] else 0
                        }
                
                db.close()
            except Exception as e:
                print(f"Profile/calorie fetch error: {e}")
        
        # Step 1: Get relevant context from RAG system with safety check
        has_food_context = food_context is not None
        retrieved_context, is_safe = rag_system.get_rag_response_context(
            user_message,
            top_k=3,  # Retrieve top 3 most relevant document chunks
            has_food_context=has_food_context
        )
        
        # Step 2: If medical question, return safety message
        if not is_safe:
            return jsonify({"response": retrieved_context})
        
        # Step 3: Build RAG-enhanced prompt with retrieved context
        system_prompt = """You are a professional health and nutrition expert assistant.

IMPORTANT INSTRUCTIONS:
1. Answer questions ONLY using information from the KNOWLEDGE BASE provided below
2. If the KNOWLEDGE BASE does not contain relevant information to answer the question, respond with:
   "I don't have specific information about that in my knowledge base. I can help you with questions about balanced diet, weight loss, hydration, post-junk food recovery, and general nutrition advice."
3. NEVER make up facts or provide information not explicitly stated in the KNOWLEDGE BASE
4. STRICTLY stay within the scope of nutrition, diet, healthy eating, and wellness
5. For questions outside this scope (physics, politics, technology, sports, entertainment, etc.), respond with:
   "I can only answer questions about nutrition, diet, healthy eating, weight management, hydration, and general wellness. Please ask a question related to these topics."
6. Be concise, practical, and supportive in your responses
7. Do NOT provide medical diagnoses or treatment for diseases
8. If there is RECENTLY ANALYZED FOOD context, treat short/follow-up questions (like "is this good for me", "should I eat it") as referring to that food
9. If TODAY'S CALORIE TRACKING data is provided, consider it when giving dietary advice (e.g., if user is close to limit, suggest lighter options)
{calorie_info}
{profile_info}
{food_info}
=== KNOWLEDGE BASE ===
{context}
======================

Based ONLY on the above knowledge base{personalization_note}{calorie_note}{food_context_note}, provide a helpful and accurate response to the user's question. If the information needed is not in the knowledge base, say so clearly."""
        
        # Add user profile info if available
        profile_info_text = ""
        personalization_note = ""
        if user_profile:
            # Calculate BMI and weight status
            height_m = user_profile['height'] / 100  # Convert cm to meters
            bmi = user_profile['weight'] / (height_m * height_m) if height_m > 0 else 0
            
            # Determine weight status
            if bmi < 18.5:
                weight_status = "Underweight"
            elif bmi < 25:
                weight_status = "Normal weight"
            elif bmi < 30:
                weight_status = "Overweight"
            else:
                weight_status = "Obese"
            
            # Calculate weight difference if target is set
            weight_diff_text = ""
            if user_profile['target_weight']:
                diff = user_profile['target_weight'] - user_profile['weight']
                if diff > 0:
                    weight_diff_text = f"(needs to gain {abs(diff):.1f} kg)"
                elif diff < 0:
                    weight_diff_text = f"(needs to lose {abs(diff):.1f} kg)"
                else:
                    weight_diff_text = "(at target weight)"
            
            profile_info_text = f"""
=== USER PROFILE & GOALS ===
Age: {user_profile['age']} years
Gender: {user_profile['gender']}
Height: {user_profile['height']} cm
Current Weight: {user_profile['weight']} kg
BMI: {bmi:.1f} ({weight_status})
Target Weight: {user_profile['target_weight'] if user_profile['target_weight'] else 'Not specified'} kg {weight_diff_text}
Activity Level: {user_profile['activity_level']}
Primary Goal: {user_profile['goal']}
Dietary Restrictions: {user_profile['dietary_restrictions'] if user_profile['dietary_restrictions'] else 'None'}
Health Conditions: {user_profile['health_conditions'] if user_profile['health_conditions'] else 'None'}

IMPORTANT: When answering questions about food or diet:
1. ALWAYS consider if the food aligns with their goal ({user_profile['goal']})
2. For weight loss goals: Recommend low-calorie, high-protein, high-fiber foods
3. For weight gain goals: Recommend calorie-dense, nutrient-rich foods
4. For muscle building: Emphasize protein intake and timing
5. Check if food conflicts with their dietary restrictions
6. Consider their health conditions when making recommendations
7. Provide specific advice based on their BMI and weight status
8. Suggest portion sizes appropriate for their goals
==================
"""
            personalization_note = " and considering the user's profile information, goals, and health status"
        
        # Add calorie tracking info if available
        calorie_info_text = ""
        calorie_note = ""
        if calorie_context:
            remaining_status = "under limit" if calorie_context['remaining'] > 0 else "OVER LIMIT"
            calorie_info_text = f"""
=== TODAY'S CALORIE TRACKING ===
Daily Target: {calorie_context['target']:.0f} kcal
Consumed So Far: {calorie_context['actual']:.0f} kcal
Remaining: {calorie_context['remaining']:.0f} kcal ({remaining_status})
Foods Logged: {calorie_context['foods_count']}

IMPORTANT: Use this data to give context-aware advice:
- If remaining calories are LOW (< 500), suggest lighter meal options
- If user is OVER LIMIT, recommend very low-calorie foods or fasting strategies
- If plenty of calories remain, user has more flexibility
- Always consider their daily goal when suggesting foods
==================
"""
            calorie_note = " and today's calorie tracking data"
        
        # Add food context if provided
        food_info_text = ""
        food_context_note = ""
        if food_context:
            food_info_text = f"""
=== RECENTLY ANALYZED FOOD ===
Food: {food_context.get('food', 'Unknown')}
Calories: {food_context.get('calories', 'N/A')}
Protein: {food_context.get('protein', 'N/A')}
Carbs: {food_context.get('carbs', 'N/A')}
Fat: {food_context.get('fat', 'N/A')}
==============================
"""
            food_context_note = " and the recently analyzed food"
        
        system_prompt = system_prompt.format(
            context=retrieved_context,
            profile_info=profile_info_text,
            calorie_info=calorie_info_text,
            food_info=food_info_text,
            personalization_note=personalization_note,
            calorie_note=calorie_note,
            food_context_note=food_context_note
        )
        
        # Step 4: Call Gemini API with RAG context
        headers = {
            "Content-Type": "application/json"
        }
        
        # Combine system prompt and user message for Gemini
        full_prompt = f"{system_prompt}\n\nUser: {user_message}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": full_prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.5,  # Lower temperature for more factual responses
                "maxOutputTokens": 500
            }
        }
        
        response = requests.post(
            f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        # Step 5: Process and return response
        if response.status_code == 200:
            response_data = response.json()
            if "candidates" in response_data and len(response_data["candidates"]) > 0 and "content" in response_data["candidates"][0] and "parts" in response_data["candidates"][0]["content"] and len(response_data["candidates"][0]["content"]["parts"]) > 0:
                bot_response = response_data["candidates"][0]["content"]["parts"][0]["text"]
                # Clean the response from markdown formatting
                bot_response = format_llm_response(bot_response)
                return jsonify({"response": bot_response})
            else:
                return jsonify({"error": "No response generated"}), 500
        else:
            print(f"Chat API error: {response.status_code} - {response.text}")
            return jsonify({"error": "Failed to get response. Please try again."}), 500
            
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({"error": "Chat service unavailable. Please try again."}), 500


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/auth")
def auth_page():
    """Serve authentication page."""
    return render_template("auth.html")


@app.route("/profile-page")
def profile_page():
    """Serve profile page."""
    return render_template("profile.html")


@app.route("/register", methods=["POST"])
def register():
    """Register a new user."""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        # Validation
        if not username or not email or not password:
            return jsonify({"error": "All fields are required"}), 400
        
        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400
        
        # Hash password
        password_hash = generate_password_hash(password)
        
        # Insert into database
        db = get_db()
        try:
            db.execute(
                'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                (username, email, password_hash)
            )
            db.commit()
            return jsonify({"message": "Registration successful! Please log in."}), 201
        except sqlite3.IntegrityError:
            return jsonify({"error": "Username or email already exists"}), 409
        finally:
            db.close()
            
    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({"error": "Registration failed. Please try again."}), 500


@app.route("/login", methods=["POST"])
def login():
    """Login user."""
    try:
        data = request.get_json()
        username_or_email = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username_or_email or not password:
            return jsonify({"error": "Please enter username/email and password"}), 400
        
        # Find user by username or email
        db = get_db()
        user = db.execute(
            'SELECT * FROM users WHERE username = ? OR email = ?',
            (username_or_email, username_or_email)
        ).fetchone()
        db.close()
        
        if user is None or not check_password_hash(user['password_hash'], password):
            return jsonify({"error": "Invalid username/email or password"}), 401
        
        # Set session
        session.clear()
        session['user_id'] = user['id']
        session['username'] = user['username']
        
        return jsonify({
            "message": "Login successful!",
            "username": user['username']
        }), 200
        
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"error": "Login failed. Please try again."}), 500


@app.route("/logout", methods=["POST"])
def logout():
    """Logout user."""
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200


@app.route("/check-auth", methods=["GET"])
def check_auth():
    """Check if user is logged in."""
    if 'user_id' in session:
        return jsonify({
            "logged_in": True,
            "username": session.get('username')
        }), 200
    else:
        return jsonify({"logged_in": False}), 200


@app.route("/profile", methods=["GET"])
@login_required
def get_profile():
    """Get user's profile information."""
    try:
        db = get_db()
        profile = db.execute(
            'SELECT * FROM user_profiles WHERE user_id = ?',
            (session['user_id'],)
        ).fetchone()
        db.close()
        
        if profile:
            return jsonify({
                "profile": {
                    "age": profile['age'],
                    "gender": profile['gender'],
                    "height": profile['height'],
                    "weight": profile['weight'],
                    "target_weight": profile['target_weight'],
                    "activity_level": profile['activity_level'],
                    "goal": profile['goal'],
                    "dietary_restrictions": profile['dietary_restrictions'],
                    "health_conditions": profile['health_conditions']
                }
            }), 200
        else:
            return jsonify({"profile": None}), 200
            
    except Exception as e:
        print(f"Profile retrieval error: {e}")
        return jsonify({"error": "Failed to retrieve profile"}), 500


@app.route("/profile", methods=["POST", "PUT"])
@login_required
def update_profile():
    """Create or update user's profile."""
    try:
        data = request.get_json()
        
        # Extract profile data
        age = data.get('age')
        gender = data.get('gender')
        height = data.get('height')
        weight = data.get('weight')
        target_weight = data.get('target_weight')
        activity_level = data.get('activity_level')
        goal = data.get('goal')
        dietary_restrictions = data.get('dietary_restrictions', '')
        health_conditions = data.get('health_conditions', '')
        
        # Validation
        if not all([age, gender, height, weight, activity_level, goal]):
            return jsonify({"error": "Please fill in all required fields"}), 400
        
        # Convert to appropriate types
        try:
            age = int(age)
            height = float(height)
            weight = float(weight)
            if target_weight:
                target_weight = float(target_weight)
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid numeric values"}), 400
        
        db = get_db()
        
        # Check if profile exists
        existing = db.execute(
            'SELECT id FROM user_profiles WHERE user_id = ?',
            (session['user_id'],)
        ).fetchone()
        
        if existing:
            # Update existing profile
            db.execute(
                '''UPDATE user_profiles 
                   SET age=?, gender=?, height=?, weight=?, target_weight=?, 
                       activity_level=?, goal=?, dietary_restrictions=?, 
                       health_conditions=?, updated_at=CURRENT_TIMESTAMP
                   WHERE user_id=?''',
                (age, gender, height, weight, target_weight, 
                 activity_level, goal, dietary_restrictions, 
                 health_conditions, session['user_id'])
            )
        else:
            # Create new profile
            db.execute(
                '''INSERT INTO user_profiles 
                   (user_id, age, gender, height, weight, target_weight, 
                    activity_level, goal, dietary_restrictions, health_conditions)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (session['user_id'], age, gender, height, weight, target_weight,
                 activity_level, goal, dietary_restrictions, health_conditions)
            )
        
        db.commit()
        db.close()
        
        return jsonify({"message": "Profile updated successfully!"}), 200
        
    except Exception as e:
        print(f"Profile update error: {e}")
        return jsonify({"error": "Failed to update profile"}), 500


@app.route("/recognize", methods=["POST"])
def recognize_food():
    # --- Step 1: Image handling ---
    if "image" not in request.files and "url" not in request.form:
        return jsonify({"error": "No image provided"}), 400

    try:
        if "image" in request.files:
            file = request.files["image"]
            image = Image.open(file.stream).convert("RGB")
        else:
            image_url = request.form.get("url")
            if not image_url:
                return jsonify({"error": "No image URL provided"}), 400
            image = Image.open(requests.get(image_url, stream=True).raw).convert("RGB")

        inputs = processor(images=image, return_tensors="pt")
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            probs = torch.nn.functional.softmax(logits, dim=-1)
            confidence = probs.max().item() * 100
            predicted_class_idx = logits.argmax(-1).item()

            # ✅ FIX: Proper label mapping for Food-101
            food_name_raw = model.config.id2label[predicted_class_idx]

            # If model gives numeric labels (like "53"), map manually
            if str(food_name_raw).isdigit():
                food101_labels = [
                    'apple_pie','baby_back_ribs','baklava','beef_carpaccio','beef_tartare',
                    'beet_salad','beignets','bibimbap','bread_pudding','breakfast_burrito',
                    'bruschetta','caesar_salad','cannoli','caprese_salad','carrot_cake',
                    'ceviche','cheesecake','cheese_plate','chicken_curry','chicken_quesadilla',
                    'chicken_wings','chocolate_cake','chocolate_mousse','churros','clam_chowder',
                    'club_sandwich','crab_cakes','creme_brulee','croque_madame','cup_cakes',
                    'deviled_eggs','donuts','dumplings','edamame','eggs_benedict','escargots',
                    'falafel','filet_mignon','fish_and_chips','foie_gras','french_fries',
                    'french_onion_soup','french_toast','fried_calamari','fried_rice','frozen_yogurt',
                    'garlic_bread','gnocchi','greek_salad','grilled_cheese_sandwich','grilled_salmon',
                    'guacamole','gyoza','hamburger','hot_and_sour_soup','hot_dog','huevos_rancheros',
                    'hummus','ice_cream','lasagna','lobster_bisque','lobster_roll_sandwich',
                    'macaroni_and_cheese','macarons','miso_soup','mussels','nachos','omelette',
                    'onion_rings','oysters','pad_thai','paella','pancakes','panna_cotta',
                    'peking_duck','pho','pizza','pork_chop','poutine','prime_rib','pulled_pork_sandwich',
                    'ramen','ravioli','red_velvet_cake','risotto','samosa','sashimi','scallops',
                    'seaweed_salad','shrimp_and_grits','spaghetti_bolognese','spaghetti_carbonara',
                    'spring_rolls','steak','strawberry_shortcake','sushi','tacos','takoyaki',
                    'tiramisu','tuna_tartare','waffles'
                ]
                idx = int(food_name_raw)
                if 0 <= idx < len(food101_labels):
                    food_name = food101_labels[idx].replace("_", " ").title()
                else:
                    food_name = f"Class {food_name_raw}"
            else:
                food_name = str(food_name_raw).replace("_", " ").title()

    except Exception as e:
        print("Food model error:", e)
        return jsonify({"error": "Failed to classify food"}), 500

    # --- Step 2: Query USDA API for nutrition data ---
    search_url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    params = {"api_key": USDA_API_KEY, "query": food_name, "pageSize": 5}

    try:
        search_resp = requests.get(search_url, params=params, timeout=15)
        search_data = search_resp.json()
    except Exception as e:
        print("USDA search error:", e)
        search_data = {}

    nutrients: Dict[str, float | str | None] = {
        "calories": None,
        "protein": None,
        "fat": None,
        "carbohydrates": None,
        "fiber": None,
        "sugar": None,
        "sodium": None,
        "cholesterol": None,
    }
    units: Dict[str, str | None] = {k: None for k in nutrients}

    def set_if_missing(key, val, unit):
        if val is not None and nutrients.get(key) is None:
            nutrients[key] = val
            units[key] = unit

    # --- Step 3: Process USDA Data ---
    if "foods" in search_data and isinstance(search_data["foods"], list):
        filtered_foods = [
            f for f in search_data["foods"]
            if f.get("dataType") in ["Foundation", "Survey (FNDDS)"]
        ] or search_data["foods"]

        for food_entry in filtered_foods:
            fdc_id = food_entry.get("fdcId")
            if not fdc_id:
                continue

            detail_url = f"https://api.nal.usda.gov/fdc/v1/food/{fdc_id}"
            try:
                detail_resp = requests.get(detail_url, params={"api_key": USDA_API_KEY}, timeout=15)
                if detail_resp.status_code != 200:
                    continue
                detail_data = detail_resp.json()
            except Exception as e:
                print("USDA detail error:", e)
                continue

            serving_size = detail_data.get("servingSize")
            serving_unit = detail_data.get("servingSizeUnit")
            scale = 1.0
            if serving_size and serving_unit and serving_unit.lower() in ["g", "gram", "grams"]:
                try:
                    scale = 100.0 / float(serving_size)
                except Exception:
                    pass

            for n in detail_data.get("foodNutrients", []):
                name, value, unit = _extract_name_value_unit(n)
                if value is None:
                    continue
                try:
                    value = float(value) * scale
                except Exception:
                    continue

                if "energy" in name:
                    if "kcal" in name or (unit and unit.upper() == "KCAL"):
                        set_if_missing("calories", round(value, 2), "kcal")
                    elif unit and unit.upper() == "KJ":
                        set_if_missing("calories", round(value / 4.184, 2), "kcal")
                elif "protein" in name:
                    set_if_missing("protein", round(value, 2), unit or "g")
                elif "fat" in name and "total" in name:
                    set_if_missing("fat", round(value, 2), unit or "g")
                elif "carbohydrate" in name:
                    set_if_missing("carbohydrates", round(value, 2), unit or "g")
                elif "fiber" in name:
                    set_if_missing("fiber", round(value, 2), unit or "g")
                elif "sugar" in name:
                    set_if_missing("sugar", round(value, 2), unit or "g")
                elif "sodium" in name:
                    set_if_missing("sodium", round(value, 2), unit or "mg")
                elif "cholesterol" in name:
                    set_if_missing("cholesterol", round(value, 2), unit or "mg")

            if all(nutrients[k] is not None for k in nutrients):
                break

    for k in nutrients.keys():
        if nutrients[k] is None:
            nutrients[k] = "N/A"
            units[k] = ""

    # --- Step 4: Get LLM dietary advice with user profile if available ---
    user_profile = None
    if 'user_id' in session:
        try:
            db = get_db()
            profile = db.execute(
                'SELECT * FROM user_profiles WHERE user_id = ?',
                (session['user_id'],)
            ).fetchone()
            db.close()
            
            if profile:
                user_profile = {
                    'age': profile['age'],
                    'gender': profile['gender'],
                    'height': profile['height'],
                    'weight': profile['weight'],
                    'target_weight': profile['target_weight'],
                    'activity_level': profile['activity_level'],
                    'goal': profile['goal'],
                    'dietary_restrictions': profile['dietary_restrictions'],
                    'health_conditions': profile['health_conditions']
                }
        except Exception as e:
            print(f"Profile fetch error: {e}")
    
    dietary_advice = get_llm_dietary_advice(food_name, nutrients, confidence, user_profile)

    # --- Step 5: Save to user history if logged in ---
    if 'user_id' in session:
        try:
            db = get_db()
            db.execute(
                '''INSERT INTO food_history 
                   (user_id, food_name, confidence, calories, protein, fat, 
                    carbohydrates, fiber, sugar, sodium, cholesterol, dietary_advice)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    session['user_id'],
                    food_name,
                    round(confidence, 2),
                    str(nutrients.get('calories', 'N/A')),
                    str(nutrients.get('protein', 'N/A')),
                    str(nutrients.get('fat', 'N/A')),
                    str(nutrients.get('carbohydrates', 'N/A')),
                    str(nutrients.get('fiber', 'N/A')),
                    str(nutrients.get('sugar', 'N/A')),
                    str(nutrients.get('sodium', 'N/A')),
                    str(nutrients.get('cholesterol', 'N/A')),
                    dietary_advice
                )
            )
            db.commit()
            db.close()
        except Exception as e:
            print(f"Error saving history: {e}")

    return jsonify({
        "food": food_name,
        "confidence": round(confidence, 2),
        "nutrients": nutrients,
        "nutrient_units": units,
        "serving": "per 100g",
        "dietary_advice": dietary_advice
    })


@app.route("/reload-knowledge", methods=["POST"])
def reload_knowledge():
    """
    Endpoint to reload knowledge base after adding new .txt files.
    Call this endpoint to refresh the RAG system without restarting the app.
    """
    try:
        rag_system.reload_knowledge_base()
        return jsonify({
            "message": "Knowledge base reloaded successfully!",
            "document_count": len(rag_system.documents)
        })
    except Exception as e:
        print(f"Reload error: {e}")
        return jsonify({"error": "Failed to reload knowledge base"}), 500


@app.route("/history", methods=["GET"])
@login_required
def get_history():
    """Get user's food analysis history."""
    try:
        db = get_db()
        history = db.execute(
            '''SELECT id, food_name, confidence, calories, protein, fat, 
                      carbohydrates, fiber, sugar, sodium, cholesterol, 
                      dietary_advice, analyzed_at
               FROM food_history 
               WHERE user_id = ? 
               ORDER BY analyzed_at DESC''',
            (session['user_id'],)
        ).fetchall()
        db.close()
        
        # Convert to list of dictionaries
        history_list = []
        for row in history:
            history_list.append({
                'id': row['id'],
                'food_name': row['food_name'],
                'confidence': row['confidence'],
                'calories': row['calories'],
                'protein': row['protein'],
                'fat': row['fat'],
                'carbohydrates': row['carbohydrates'],
                'fiber': row['fiber'],
                'sugar': row['sugar'],
                'sodium': row['sodium'],
                'cholesterol': row['cholesterol'],
                'dietary_advice': row['dietary_advice'],
                'analyzed_at': row['analyzed_at']
            })
        
        return jsonify({
            "history": history_list,
            "count": len(history_list)
        }), 200
        
    except Exception as e:
        print(f"History retrieval error: {e}")
        return jsonify({"error": "Failed to retrieve history"}), 500


@app.route("/history/<int:history_id>", methods=["DELETE"])
@login_required
def delete_history_item(history_id):
    """Delete a specific history item."""
    try:
        db = get_db()
        result = db.execute(
            'DELETE FROM food_history WHERE id = ? AND user_id = ?',
            (history_id, session['user_id'])
        )
        db.commit()
        db.close()
        
        if result.rowcount == 0:
            return jsonify({"error": "History item not found"}), 404
        
        return jsonify({"message": "History item deleted successfully"}), 200
        
    except Exception as e:
        print(f"Delete history error: {e}")
        return jsonify({"error": "Failed to delete history item"}), 500


@app.route("/calorie-today", methods=["GET"])
@login_required
def get_today_calories():
    """Get today's calorie tracking data."""
    try:
        from datetime import date
        today = str(date.today())
        
        db = get_db()
        
        # Get user profile to calculate target
        profile = db.execute(
            'SELECT * FROM user_profiles WHERE user_id = ?',
            (session['user_id'],)
        ).fetchone()
        
        if not profile:
            db.close()
            return jsonify({
                "target_calories": 2000,
                "actual_calories": 0,
                "foods_eaten": [],
                "remaining_calories": 2000,
                "progress_percentage": 0,
                "has_profile": False
            }), 200
        
        user_profile = {
            'age': profile['age'],
            'gender': profile['gender'],
            'weight': profile['weight'],
            'height': profile['height'],
            'activity_level': profile['activity_level'],
            'goal': profile['goal']
        }
        
        target_calories = calculate_daily_calorie_target(user_profile)
        
        # Get or create today's log
        log = db.execute(
            'SELECT * FROM daily_calorie_log WHERE user_id = ? AND log_date = ?',
            (session['user_id'], today)
        ).fetchone()
        
        if log:
            actual_calories = log['actual_calories']
            foods_eaten = json.loads(log['foods_eaten']) if log['foods_eaten'] else []
        else:
            actual_calories = 0
            foods_eaten = []
            # Create today's log
            db.execute(
                'INSERT INTO daily_calorie_log (user_id, log_date, target_calories, actual_calories, foods_eaten) VALUES (?, ?, ?, ?, ?)',
                (session['user_id'], today, target_calories, 0, json.dumps([]))
            )
            db.commit()
        
        db.close()
        
        remaining = target_calories - actual_calories
        progress = min((actual_calories / target_calories) * 100, 100) if target_calories > 0 else 0
        
        return jsonify({
            "target_calories": target_calories,
            "actual_calories": actual_calories,
            "remaining_calories": remaining,
            "foods_eaten": foods_eaten,
            "progress_percentage": round(progress, 1),
            "has_profile": True,
            "date": today
        }), 200
        
    except Exception as e:
        print(f"Calorie tracking error: {e}")
        return jsonify({"error": "Failed to get calorie data"}), 500


@app.route("/log-food", methods=["POST"])
@login_required
def log_food_manually():
    """Manually log a food item (I'm eating this button)."""
    try:
        from datetime import date
        today = str(date.today())
        
        data = request.get_json()
        food_name = data.get('food_name', '').strip()
        calories = data.get('calories', 0)
        
        if not food_name:
            return jsonify({"error": "Food name is required"}), 400
        
        # Try to parse calories as number
        try:
            calories = float(calories) if calories else 0
        except (ValueError, TypeError):
            calories = 0
        
        db = get_db()
        
        # Get user profile
        profile = db.execute(
            'SELECT * FROM user_profiles WHERE user_id = ?',
            (session['user_id'],)
        ).fetchone()
        
        if not profile:
            db.close()
            return jsonify({"error": "Please complete your profile first"}), 400
        
        user_profile = {
            'age': profile['age'],
            'gender': profile['gender'],
            'weight': profile['weight'],
            'height': profile['height'],
            'activity_level': profile['activity_level'],
            'goal': profile['goal']
        }
        
        target_calories = calculate_daily_calorie_target(user_profile)
        
        # Get or create today's log
        log = db.execute(
            'SELECT * FROM daily_calorie_log WHERE user_id = ? AND log_date = ?',
            (session['user_id'], today)
        ).fetchone()
        
        if log:
            current_actual = log['actual_calories']
            current_foods = json.loads(log['foods_eaten']) if log['foods_eaten'] else []
            
            new_actual = current_actual + calories
            current_foods.append({
                'name': food_name,
                'calories': calories,
                'logged_at': datetime.now().strftime('%H:%M')
            })
            
            db.execute(
                '''UPDATE daily_calorie_log 
                   SET actual_calories = ?, foods_eaten = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE user_id = ? AND log_date = ?''',
                (new_actual, json.dumps(current_foods), session['user_id'], today)
            )
        else:
            new_actual = calories
            foods_list = [{
                'name': food_name,
                'calories': calories,
                'logged_at': datetime.now().strftime('%H:%M')
            }]
            
            db.execute(
                'INSERT INTO daily_calorie_log (user_id, log_date, target_calories, actual_calories, foods_eaten) VALUES (?, ?, ?, ?, ?)',
                (session['user_id'], today, target_calories, new_actual, json.dumps(foods_list))
            )
        
        db.commit()
        db.close()
        
        remaining = target_calories - new_actual
        
        return jsonify({
            "message": f"{food_name} logged successfully!",
            "food_name": food_name,
            "calories_added": calories,
            "total_calories": new_actual,
            "target_calories": target_calories,
            "remaining_calories": remaining,
            "progress_percentage": round(min((new_actual / target_calories) * 100, 100), 1) if target_calories > 0 else 0
        }), 200
        
    except Exception as e:
        print(f"Log food error: {e}")
        return jsonify({"error": "Failed to log food"}), 500


if __name__ == "__main__":
    app.run(debug=True)
