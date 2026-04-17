# Daily Calorie Tracker - Complete Feature Guide

## 🎯 Overview

The NutriNova AI now includes a **comprehensive daily calorie tracking system** that:
- ✅ Calculates personalized daily calorie targets based on your profile
- ✅ Tracks actual calorie intake throughout the day
- ✅ Shows visual progress with a calorie meter
- ✅ Allows manual food logging with "I'm Eating This" button
- ✅ Integrates calorie data into AI chat for smarter recommendations
- ✅ Displays today's logged foods with timestamps

---

## 🔥 How It Works

### 1. Personalized Calorie Target Calculation

The system uses the **Mifflin-St Jeor Equation** (most accurate BMR formula) to calculate your daily calorie needs:

#### Step 1: Calculate BMR (Basal Metabolic Rate)
```
For Men:   BMR = (10 × weight) + (6.25 × height) - (5 × age) + 5
For Women: BMR = (10 × weight) + (6.25 × height) - (5 × age) - 161
```

#### Step 2: Apply Activity Multiplier
- Sedentary (little exercise): × 1.2
- Lightly Active (1-3 days/week): × 1.375
- Moderately Active (3-5 days/week): × 1.55
- Very Active (6-7 days/week): × 1.725
- Extra Active (physical job): × 1.9

#### Step 3: Adjust for Goal
- **Lose Weight**: TDEE - 500 calories (~0.5kg/week loss)
- **Gain Weight**: TDEE + 500 calories (~0.5kg/week gain)
- **Build Muscle**: TDEE + 300 calories (moderate surplus)
- **Maintain**: TDEE (no adjustment)

#### Example Calculation:
```
User Profile:
- Female, 28 years
- Height: 165 cm, Weight: 75 kg
- Activity: Moderately Active
- Goal: Lose Weight

BMR = (10 × 75) + (6.25 × 165) - (5 × 28) - 161
    = 750 + 1031.25 - 140 - 161
    = 1480.25 kcal/day

TDEE = 1480.25 × 1.55 = 2294 kcal/day

Target = 2294 - 500 = 1794 kcal/day
```

---

### 2. "I'm Eating This" Button

After analyzing any food, logged-in users see a bright green button:

```
┌─────────────────────────────────────┐
│  ✅ I'm Eating This                 │
└─────────────────────────────────────┘
```

**When clicked:**
1. Confirms food name and calories
2. Adds to today's calorie log
3. Updates actual intake total
4. Shows remaining calories
5. Stores timestamp for tracking

**Example Flow:**
```
User analyzes: Pizza (266 kcal/100g)
Clicks: "I'm Eating This"
Confirms: "Log 'Pizza' (266 kcal) to your daily tracker?"

System Response:
✅ Pizza logged successfully!

📊 Total: 266 / 1794 kcal
🎯 1528 kcal remaining today
```

---

### 3. Calorie Meter Dashboard

Access via **History** button in navigation. Shows:

#### Visual Components:

**A. Calorie Summary Cards**
```
┌──────────────┬──────────────┬──────────────┐
│ Actual Intake│   Target     │  Remaining   │
│   1,250      │   1,794      │    544       │
└──────────────┴──────────────┴──────────────┘
```

**B. Progress Bar**
- Visual bar showing percentage of target consumed
- Color-coded:
  - 🟢 Green (0-85%): On track
  - 🟠 Orange (85-100%): Almost at limit
  - 🔴 Red (>100%): Exceeded target

**C. Status Message**
- "✅ On track!" (under 85%)
- "⚡ Almost at your limit!" (85-100%)
- "⚠️ You've exceeded your target!" (>100%)

**D. Foods Logged Today**
```
Foods Logged Today (5)
┌────────────────────────────────────────┐
│ 🍕 Pizza                  266 kcal     │
│    ⏰ 14:30                            │
├────────────────────────────────────────┤
│ 🥗 Caesar Salad           184 kcal     │
│    ⏰ 12:15                            │
├────────────────────────────────────────┤
│ ☕ Latte                   120 kcal     │
│    ⏰ 09:00                            │
└────────────────────────────────────────┘
```

---

### 4. Smart Chat Integration

The AI assistant now considers your **daily calorie status** when giving advice:

#### Scenario 1: Plenty of Calories Remaining
```
User Profile:
- Target: 1800 kcal
- Consumed: 800 kcal (44%)
- Remaining: 1000 kcal

User asks: "What should I have for dinner?"

AI Response:
"You have 1000 kcal remaining, which gives you good flexibility!

Given your weight loss goal, I recommend a balanced dinner around 
600-700 kcal:

✅ Grilled salmon (350 kcal) + quinoa (200 kcal) + steamed veggies (50 kcal)
✅ Chicken stir-fry with brown rice (650 kcal)
✅ Turkey burger with sweet potato fries (700 kcal)

This leaves 300-400 kcal for a light evening snack if needed."
```

#### Scenario 2: Low Remaining Calories
```
User Profile:
- Target: 1800 kcal
- Consumed: 1450 kcal (81%)
- Remaining: 350 kcal

User asks: "Can I eat pasta tonight?"

AI Response:
"⚠️ You only have 350 kcal remaining today.

Regular pasta (130 kcal/100g) might exceed your limit if portions 
aren't controlled.

Better options for YOUR situation:
✅ Zucchini noodles (20 kcal) with marinara (80 kcal) = 100 kcal total
✅ Shirataki noodles (10 kcal) with light sauce = 50 kcal total
✅ Small portion (50g dry) whole wheat pasta = 175 kcal

If you really want regular pasta:
- Limit to 60g dry weight (230 kcal)
- Skip bread/appetizers
- Make it your last meal of the day"
```

#### Scenario 3: Over Calorie Limit
```
User Profile:
- Target: 1800 kcal
- Consumed: 2100 kcal (117%)
- Remaining: -300 kcal (OVER LIMIT)

User asks: "I'm still hungry, what can I eat?"

AI Response:
"⚠️ You've exceeded your target by 300 kcal today.

Since you're still hungry, focus on ZERO or very low-calorie options:

✅ Cucumber slices (16 kcal/cup)
✅ Celery sticks (14 kcal/cup)
✅ Lettuce wraps with mustard (10 kcal)
✅ Herbal tea (0 kcal)
✅ Pickles (15 kcal/spear)

These will help satisfy hunger without adding significant calories.

Tomorrow's strategy:
- Start with high-protein breakfast (keeps you full longer)
- Drink water before meals
- Focus on volume eating (lots of veggies)
- Stay within your 1800 kcal target"
```

---

## 📊 Database Structure

### Daily Calorie Log Table
```sql
CREATE TABLE daily_calorie_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    log_date DATE NOT NULL,              -- e.g., "2025-04-06"
    target_calories REAL,                -- Calculated from profile
    actual_calories REAL DEFAULT 0,      -- Sum of logged foods
    foods_eaten TEXT,                    -- JSON array of food objects
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(user_id, log_date),           -- One entry per user per day
    FOREIGN KEY (user_id) REFERENCES users (id)
)
```

### Foods Eaten JSON Structure
```json
[
  {
    "name": "Pizza",
    "calories": 266,
    "logged_at": "14:30"
  },
  {
    "name": "Caesar Salad",
    "calories": 184,
    "logged_at": "12:15"
  }
]
```

---

## 🔧 API Endpoints

### GET /calorie-today
Get today's calorie tracking data.

**Response:**
```json
{
  "target_calories": 1794,
  "actual_calories": 1250,
  "remaining_calories": 544,
  "foods_eaten": [
    {"name": "Pizza", "calories": 266, "logged_at": "14:30"},
    {"name": "Salad", "calories": 184, "logged_at": "12:15"}
  ],
  "progress_percentage": 69.7,
  "has_profile": true,
  "date": "2025-04-06"
}
```

---

### POST /log-food
Manually log a food item.

**Request Body:**
```json
{
  "food_name": "Apple",
  "calories": 95
}
```

**Response:**
```json
{
  "message": "Apple logged successfully!",
  "food_name": "Apple",
  "calories_added": 95,
  "total_calories": 1345,
  "target_calories": 1794,
  "remaining_calories": 449,
  "progress_percentage": 75.0
}
```

---

## 💡 User Experience Flow

### Complete Journey:

1. **User logs in** → Session established
2. **Completes profile** → Age, weight, height, goal, activity level
3. **System calculates target** → e.g., 1800 kcal/day for weight loss
4. **Analyzes food image** → Pizza detected, 266 kcal/100g
5. **Clicks "I'm Eating This"** → Confirms logging
6. **Calories added to today's total** → 0 → 266 kcal
7. **Opens History** → Sees calorie meter dashboard
8. **Progress bar shows** → 15% of target consumed
9. **Asks chatbot** → "What's a good dinner option?"
10. **AI considers remaining calories** → Suggests appropriate meals
11. **Logs more foods** → Total increases throughout day
12. **Ends day** → Can review all logged foods with timestamps

---

## 🎨 UI Features

### Calorie Meter Design
- **Large numbers** for easy reading
- **Color-coded** based on progress
- **Animated progress bar** with smooth transitions
- **Responsive layout** works on mobile
- **Scrollable food list** for many entries
- **Timestamp display** for each logged food

### "I'm Eating This" Button
- **Bright lime green** gradient for visibility
- **Check icon** for positive action
- **Hover effects** for interactivity
- **Only shows when logged in**
- **Confirmation dialog** prevents accidental logging

---

## 🚀 Advanced Features

### 1. Automatic Daily Reset
- New log entry created automatically each day
- Previous day's data preserved in database
- No manual reset needed

### 2. Profile-Based Targets
- Recalculates if user updates profile
- Adjusts for weight changes
- Updates when goal changes

### 3. Smart Warnings
- Alerts when approaching limit (85%+)
- Warns when exceeding target
- Suggests corrective actions

### 4. Chat Context Awareness
- AI knows your remaining calories
- Suggests foods that fit your budget
- Provides alternatives if over limit

---

## 📈 Benefits

### For Users:
✅ **Awareness**: See exactly how much you've eaten
✅ **Accountability**: Visual progress motivates better choices
✅ **Personalization**: Targets based on YOUR body and goals
✅ **Convenience**: One-click logging from food analysis
✅ **Smart Advice**: AI considers your daily calorie status
✅ **Historical Data**: Track patterns over time

### For Weight Goals:
✅ **Weight Loss**: Stay in calorie deficit consistently
✅ **Weight Gain**: Ensure adequate calorie surplus
✅ **Maintenance**: Hit target calories daily
✅ **Muscle Building**: Support growth with proper nutrition

---

## 🔒 Privacy & Data

- All calorie data stored securely in database
- Only accessible to authenticated user
- Can be deleted anytime
- Not shared with third parties
- Daily logs preserved for future analytics

---

## 🎯 Example Use Cases

### Case 1: Strict Dieter
```
Goal: Lose 10 kg
Target: 1500 kcal/day

Morning: Logs breakfast (350 kcal)
Afternoon: Analyzes lunch, logs it (450 kcal)
Evening: Checks meter → 800/1500 kcal (700 remaining)
Chat: "What's a light dinner?"
AI: Suggests 500-600 kcal meal with veggies and lean protein
Result: Stays within target, achieves deficit
```

### Case 2: Muscle Builder
```
Goal: Gain 5 kg muscle
Target: 2800 kcal/day

Tracks all meals meticulously
Mid-day: Already at 1800 kcal (1000 remaining)
Chat: "Need more calories, suggestions?"
AI: Recommends calorie-dense healthy snacks (nuts, avocado, smoothies)
Result: Hits surplus target for muscle growth
```

### Case 3: Maintenance
```
Goal: Maintain current weight
Target: 2200 kcal/day

Casual tracking, not strict
Some days over, some under
Weekly average: ~2200 kcal/day
Result: Weight stays stable
```

---

## 💻 Technical Implementation

### Files Modified:
1. **app.py**
   - Added `daily_calorie_log` table
   - `calculate_daily_calorie_target()` function
   - `/calorie-today` endpoint
   - `/log-food` endpoint
   - Updated `/chat` to include calorie context

2. **templates/index.html**
   - "I'm Eating This" button in results
   - `logThisFood()` JavaScript function
   - Calorie meter dashboard UI
   - `loadCalorieMeter()` and `displayCalorieDashboard()` functions
   - Enhanced history modal with calorie tracking

### Key Algorithms:
- Mifflin-St Jeor BMR calculation
- Activity level multipliers
- Goal-based adjustments
- Progress percentage calculation
- Color-coding logic

---

## ❓ FAQ

**Q: How accurate is the calorie target?**
A: The Mifflin-St Jeor equation is 90%+ accurate for most people. Adjust based on real-world results.

**Q: Can I edit logged foods?**
A: Currently no, but you can delete and re-log if needed. Edit feature coming soon.

**Q: What if I don't know the calories?**
A: The system uses USDA data from food analysis. For manual entry, estimate or use 0.

**Q: Does it reset automatically?**
A: Yes, new log created each day at midnight.

**Q: Can I see past days?**
A: Data is saved in database. Weekly/monthly views coming in future updates.

**Q: What if my weight changes?**
A: Update your profile, and the target recalculates automatically.

---

## 🎉 Summary

The Daily Calorie Tracker transforms NutriNova AI into a **complete nutrition management system**:

- 🔥 **Smart Targets**: Personalized using scientific formulas
- 📊 **Visual Tracking**: Beautiful meter with progress bars
- ⚡ **Quick Logging**: One-click "I'm Eating This" button
- 🤖 **AI Integration**: Chat considers your calorie status
- 📱 **Mobile Friendly**: Works on all devices
- 🔒 **Secure**: Your data stays private

**Result:** A powerful tool that helps you achieve your weight goals through informed, tracked, and personalized nutrition!
