# Personalized AI Nutrition Assistant - Feature Guide

## Overview
The NutriNova AI now provides **highly personalized nutrition advice** based on your complete health profile. The AI assistant considers your age, gender, body measurements, fitness goals, dietary restrictions, and health conditions to give tailored recommendations.

## 🎯 How Personalization Works

### 1. User Profile Data Collection
When you fill out your profile at `/profile-page`, the system collects:

#### Basic Information
- **Age**: Affects metabolism and nutritional needs
- **Gender**: Different nutritional requirements for males/females

#### Body Measurements
- **Height & Weight**: Used to calculate BMI
- **Target Weight**: Determines if you need to gain/lose weight
- **BMI Calculation**: Automatically calculated to assess current health status

#### Goals & Lifestyle
- **Primary Goal**: 
  - Lose Weight
  - Gain Weight
  - Maintain Weight
  - Build Muscle
  - Improve Overall Health
- **Activity Level**: From sedentary to extra active (affects calorie needs)

#### Health Details
- **Dietary Restrictions**: Vegetarian, vegan, allergies, intolerances
- **Health Conditions**: Diabetes, PCOS, thyroid issues, etc.

---

### 2. AI Chat Personalization

When you chat with the AI assistant, it automatically:

#### ✅ Considers Your Goals
```
Example: If your goal is "Lose Weight"
- Recommends low-calorie, high-protein foods
- Suggests appropriate portion sizes
- Warns about high-calorie foods
- Provides calorie deficit strategies
```

#### ✅ Analyzes Your BMI
```
BMI Categories:
- Underweight (< 18.5): Focus on healthy weight gain
- Normal (18.5-24.9): Maintain balanced diet
- Overweight (25-29.9): Moderate calorie reduction
- Obese (30+): Structured weight loss plan
```

#### ✅ Checks Dietary Restrictions
```
If you're vegetarian:
- Won't recommend meat-based proteins
- Suggests plant-based alternatives
- Ensures adequate protein intake from legumes, nuts, etc.
```

#### ✅ Considers Health Conditions
```
If you have diabetes:
- Avoids high-sugar recommendations
- Focuses on low glycemic index foods
- Emphasizes fiber-rich options
```

#### ✅ Calculates Weight Difference
Shows exactly how much weight you need to gain/lose to reach your target.

---

### 3. Food Analysis Personalization

When you analyze a food image while logged in:

#### Personalized Assessment
The AI evaluates the food based on YOUR specific goals:

**For Weight Loss Users:**
```
Food: Pizza
Assessment:
- For Weight Loss: Not Recommended - High in calories (266 kcal/100g) 
  and saturated fat. Consider having 1 slice instead of whole pizza, 
  paired with a large salad to reduce overall calorie intake.
  
- For Weight Gain: Good - Calorie-dense option that can help with 
  surplus. Add extra cheese or pair with garlic bread for more calories.
```

**For Muscle Building Users:**
```
Food: Grilled Chicken Breast
Assessment:
- Excellent choice! High in protein (31g/100g) with low fat.
- Perfect for post-workout recovery.
- Recommended portion: 150-200g for optimal protein synthesis.
```

**For Users with Dietary Restrictions:**
```
If lactose intolerant and analyzing cheese:
⚠️ Warning: This food contains dairy which conflicts with your 
lactose intolerance. Consider lactose-free cheese alternatives 
or nutritional yeast for similar flavor.
```

---

## 📊 Example Scenarios

### Scenario 1: Weight Loss Journey
**User Profile:**
- Age: 28, Female
- Height: 165 cm, Weight: 75 kg
- Target: 65 kg (needs to lose 10 kg)
- Goal: Lose Weight
- Activity: Moderately Active

**Chat Question:** "Is pasta good for dinner?"

**Personalized Response:**
```
Based on your profile (75 kg, targeting 65 kg):

Regular pasta is moderate for weight loss. Here's why:
- 100g cooked pasta = ~130 calories
- High in carbs, which can spike blood sugar

Better options for YOUR goal:
✅ Whole wheat pasta (more fiber, keeps you full longer)
✅ Zucchini noodles (only 20 calories/100g vs 130 for regular)
✅ Portion control: Limit to 80g dry weight (~300 calories)

Tips for you:
- Pair with lean protein (grilled chicken, shrimp)
- Load up on vegetables for volume
- Avoid creamy sauces (high calorie)
- Choose tomato-based sauces instead

Given your activity level (moderate), you can include pasta 
2-3 times per week if portions are controlled.
```

---

### Scenario 2: Muscle Building
**User Profile:**
- Age: 24, Male
- Height: 180 cm, Weight: 70 kg
- Target: 78 kg (needs to gain 8 kg)
- Goal: Build Muscle
- Activity: Very Active

**Food Analysis:** Greek Yogurt

**Personalized Assessment:**
```
Excellent choice for YOUR muscle-building goal!

Why it's perfect for you:
✅ High protein: 10g per 100g (supports muscle repair)
✅ Moderate calories: 59 kcal/100g (easy to consume in larger amounts)
✅ Contains casein protein (slow-digesting, great before bed)

Recommendation for YOUR goals:
- Consume 200-250g post-workout
- Add honey and nuts for extra calories (you need surplus)
- Great bedtime snack for overnight muscle recovery
- Combine with fruits for additional carbs

To gain 8 kg of muscle, you need:
- Daily surplus: ~300-500 calories above maintenance
- Protein intake: 1.6-2.2g per kg body weight = 112-154g/day
- This yogurt provides 20-25g protein per serving
```

---

### Scenario 3: Health Condition Management
**User Profile:**
- Age: 45, Female
- BMI: 28 (Overweight)
- Goal: Lose Weight
- Health Condition: Type 2 Diabetes
- Dietary Restriction: Low-carb

**Chat Question:** "Can I eat bananas?"

**Personalized Response:**
```
⚠️ Important consideration for YOUR health profile:

Given your Type 2 Diabetes and weight loss goal:

Bananas are MODERATE for you because:
- Medium banana = 27g carbs (may spike blood sugar)
- Glycemic Index: 51 (medium)
- Contains natural sugars

Safer approach for YOU:
✅ Half a small banana (reduce carb load)
✅ Choose slightly green bananas (lower GI than ripe ones)
✅ Always pair with protein/fat (e.g., almond butter)
✅ Better alternatives: Berries (lower carb, high fiber)

Blood sugar management tips:
- Monitor glucose 2 hours after eating
- Best time: Post-workout when insulin sensitivity is higher
- Avoid on empty stomach

For weight loss + diabetes:
Focus on: Leafy greens, non-starchy vegetables, lean proteins
Limit: High-sugar fruits, refined carbs, processed foods
```

---

## 🔧 Technical Implementation

### Profile Data Flow
```
User fills profile → Stored in database → Retrieved during chat/analysis → 
Sent to AI as context → Personalized response generated
```

### BMI Calculation
```python
height_m = height_cm / 100
bmi = weight_kg / (height_m * height_m)

Categories:
- < 18.5: Underweight
- 18.5-24.9: Normal
- 25-29.9: Overweight
- ≥ 30: Obese
```

### Weight Difference
```python
difference = target_weight - current_weight

If positive: "Needs to gain X kg"
If negative: "Needs to lose X kg"
If zero: "At target weight"
```

### AI Prompt Enhancement
The system adds this context to every AI query:
```
=== USER PROFILE & GOALS ===
[BMI, weight status, target, goals, restrictions, conditions]

IMPORTANT INSTRUCTIONS:
1. Consider if food aligns with their goal
2. For weight loss: Recommend low-calorie, high-protein foods
3. For weight gain: Recommend calorie-dense, nutrient-rich foods
4. Check dietary restrictions
5. Consider health conditions
6. Provide BMI-specific advice
7. Suggest appropriate portion sizes
```

---

## 💡 Best Practices

### For Users
1. **Complete Your Profile**: More data = better personalization
2. **Be Honest**: Accurate weight/height gives correct BMI
3. **Update Regularly**: Change weight as you progress
4. **Specify Restrictions**: List all allergies/intolerances
5. **Mention Conditions**: Helps AI avoid harmful suggestions

### For Optimal Results
- Update weight weekly for accurate tracking
- Be specific about dietary preferences
- Mention any medications affecting nutrition
- Update goals as you achieve them
- Provide feedback on recommendations

---

## 🎨 User Interface Features

### Profile Page (`/profile-page`)
- Clean, modern form with all health metrics
- Real-time validation
- Auto-loads existing data
- Success/error messages
- Responsive design

### Navigation Updates
When logged in, navbar shows:
- 👤 **Profile** link to edit health data
- 📊 **History** to view past analyses
- 🚪 **Logout** to end session

### Chat Integration
- No visible changes to UI
- Backend automatically includes profile
- Responses reference your goals
- Context-aware recommendations

---

## 🔒 Privacy & Security

### Data Protection
- All profile data encrypted in database
- Only accessible to authenticated user
- Never shared with third parties
- Can be deleted anytime

### User Control
- Edit profile anytime
- Remove specific fields
- Delete entire account
- Export your data

---

## 🚀 Future Enhancements

Planned improvements:
1. **Progress Tracking**: Charts showing weight/BMI over time
2. **Meal Planning**: AI-generated meal plans based on goals
3. **Calorie Calculator**: Daily calorie needs based on profile
4. **Macro Recommendations**: Protein/carb/fat targets
5. **Workout Integration**: Exercise suggestions matching goals
6. **Water Intake Tracker**: Personalized hydration goals
7. **Sleep Tracking**: Impact on nutrition and weight
8. **Community Features**: Share progress (optional)

---

## 📝 API Endpoints

### Get Profile
```
GET /profile
Response: { profile: { age, gender, height, weight, ... } }
```

### Update Profile
```
POST /profile
Body: { age: 25, gender: "male", height: 175, weight: 70, ... }
Response: { message: "Profile updated successfully!" }
```

### Chat with Personalization
```
POST /chat
Body: { message: "What should I eat?" }
(Automatically includes user profile in background)
Response: { response: "Based on your goal to lose weight..." }
```

---

## ❓ FAQ

**Q: Do I need to fill out my profile?**
A: No, but without it, you'll get generic advice. Profile enables personalization.

**Q: Is my health data secure?**
A: Yes, all data is stored securely and only you can access it.

**Q: Can I change my profile later?**
A: Yes, update it anytime at `/profile-page`.

**Q: What if I don't know my target weight?**
A: Leave it blank. The AI will still provide general advice based on your current stats.

**Q: Does the AI replace a doctor?**
A: No. Always consult healthcare professionals for medical conditions.

**Q: How often should I update my weight?**
A: Weekly updates give the best tracking and most relevant advice.

---

## 🎯 Summary

The personalized AI nutrition assistant:
- ✅ Calculates and tracks your BMI
- ✅ Tailors advice to your specific goals
- ✅ Considers dietary restrictions
- ✅ Accounts for health conditions
- ✅ Provides goal-specific food assessments
- ✅ Recommends appropriate portion sizes
- ✅ Tracks progress toward target weight
- ✅ Gives safer, more relevant recommendations

**Result:** Nutrition advice that actually fits YOUR life, YOUR body, and YOUR goals!
