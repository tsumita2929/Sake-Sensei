# Sake Sensei User Guide

Welcome to Sake Sensei, your AI-powered Japanese sake discovery companion!

## Table of Contents

1. [Getting Started](#getting-started)
2. [Account Setup](#account-setup)
3. [Features Overview](#features-overview)
4. [How to Use](#how-to-use)
5. [FAQ](#faq)
6. [Support](#support)

## Getting Started

Sake Sensei helps you discover Japanese sake tailored to your preferences using AI-powered recommendations.

### What You'll Need

- A web browser (Chrome, Firefox, Safari, or Edge)
- Email address for account creation
- (Optional) Smartphone camera for label recognition

### Accessing Sake Sensei

Visit the application at:
- **Development:** `http://sakese-Publi-5SDe3QrKne55-1360562030.us-west-2.elb.amazonaws.com`
- **Production:** `https://sakesensei.com` (when configured)

## Account Setup

### Creating an Account

1. Click **"Sign Up"** on the home page
2. Enter your email address
3. Create a password (minimum 8 characters, must include uppercase, number, and special character)
4. Click **"Create Account"**
5. Check your email for verification code
6. Enter the 6-digit code to verify your account

### Signing In

1. Click **"Sign In"** on the home page
2. Enter your email and password
3. Click **"Sign In"**

### Password Reset

If you forget your password:

1. Click **"Forgot Password?"** on the sign-in page
2. Enter your email address
3. Check your email for reset code
4. Enter the code and create a new password

## Features Overview

### 🎯 Preference Survey

Tell us about your taste preferences:
- Sake type preferences (純米酒, 吟醸, 大吟醸, etc.)
- Flavor profile (sweet vs. dry, aromatic vs. subtle)
- Drinking context (with meals, celebrations, casual)
- Food pairing preferences

### 🤖 AI Recommendations

Get personalized sake recommendations powered by Claude 4.5 Sonnet:
- Tailored to your taste profile
- Based on your tasting history
- Conversational interface for questions
- Detailed sake information (brewery, region, characteristics)

### ⭐ Rating & Reviews

Record your tasting experiences:
- Overall rating (1-5 stars)
- Detailed ratings (aroma, taste, finish)
- Tasting notes and comments
- Add photos
- Save favorites

### 📸 Image Recognition

Identify sake from label photos:
- Take a photo of the sake label
- AI extracts sake name and brewery
- Get instant information
- Add to your tasting records

### 📚 History & Statistics

Track your sake journey:
- View all tasting records
- Statistics (total tastings, favorites, breweries explored)
- Visual charts (rating distribution, type preferences, timeline)
- Export data (CSV, JSON, summary reports)

## How to Use

### Step 1: Complete Your Preference Survey

On first login:

1. Navigate to **"Preference Survey"** page
2. Select your preferred sake types
3. Adjust flavor profile sliders:
   - **甘口 ←→ 辛口** (Sweet ←→ Dry)
   - **香り高い ←→ 控えめ** (Aromatic ←→ Subtle)
   - **軽い ←→ 濃厚** (Light ←→ Rich)
4. Choose drinking contexts
5. Select food pairing preferences
6. Click **"Save Preferences"**

### Step 2: Get AI Recommendations

1. Navigate to **"AI Recommendations"** page
2. Chat with the AI assistant:
   - "Recommend a sake for dinner with sushi"
   - "I want something fruity and aromatic"
   - "Show me sake similar to 獺祭"
3. Browse recommended sake cards
4. Click on a sake card to see details:
   - Brewery information
   - Flavor profile
   - Food pairing suggestions
   - User ratings

### Step 3: Rate Sake You've Tried

1. Navigate to **"Rating"** page
2. Search for the sake by name or select from list
3. Rate the sake:
   - **Overall Rating:** 1-5 stars
   - **Aroma:** Intensity and character
   - **Taste:** Sweetness, acidity, umami
   - **Finish:** Length and complexity
4. Add tasting notes:
   - Where you drank it
   - What you paired it with
   - Your impressions
5. Upload photos (optional)
6. Click **"Save Record"**

### Step 4: Use Image Recognition

1. Navigate to **"Image Recognition"** page
2. Take or upload a photo of the sake label
3. AI analyzes the image:
   - Extracts sake name
   - Identifies brewery
   - Provides information
4. Option to add to tasting records directly

### Step 5: Review Your History

1. Navigate to **"History"** page
2. View statistics:
   - Total tastings
   - Favorite sake
   - Breweries explored
   - Average rating
3. Browse tasting records:
   - Filter by date range
   - Filter by sake type
   - Filter by rating
4. View charts:
   - Rating distribution (bar chart)
   - Sake type preferences (pie chart)
   - Tasting timeline (line chart)
5. Export your data:
   - **CSV:** For Excel/Google Sheets
   - **JSON:** For data analysis
   - **Summary:** Text report

## Tips & Best Practices

### For Better Recommendations

- Update your preference survey as your tastes evolve
- Rate sake consistently using the same criteria
- Add detailed tasting notes (the AI learns from these)
- Try recommended sake outside your usual preferences

### Recording Tastings

- Record tastings soon after (while fresh in memory)
- Include context (temperature, food pairing, occasion)
- Be honest in ratings (helps improve recommendations)
- Add photos to remember the experience

### Using the AI Assistant

- Ask specific questions ("sake for grilled fish")
- Mention preferences ("I like dry sake")
- Describe previous favorites ("similar to 久保田")
- Ask for explanations ("why do you recommend this?")

## FAQ

### General Questions

**Q: Is Sake Sensei free to use?**
A: Yes, Sake Sensei is currently free for all users.

**Q: Do I need to be a sake expert?**
A: No! Sake Sensei is designed for everyone from beginners to connoisseurs.

**Q: How accurate are the AI recommendations?**
A: Recommendations improve as you rate more sake and update your preferences.

### Account & Privacy

**Q: Is my data secure?**
A: Yes, we use AWS Cognito for authentication and follow security best practices.

**Q: Can I delete my account?**
A: Contact support at support@sakesensei.com for account deletion.

**Q: Who can see my ratings?**
A: Your ratings are private and only visible to you.

### Technical Questions

**Q: What browsers are supported?**
A: Modern versions of Chrome, Firefox, Safari, and Edge.

**Q: Can I use Sake Sensei on mobile?**
A: Yes! The web app is mobile-friendly and works on smartphones and tablets.

**Q: Do I need to install anything?**
A: No, Sake Sensei is a web application. Just visit the URL in your browser.

**Q: Does the image recognition work offline?**
A: No, image recognition requires an internet connection.

### Sake Information

**Q: How many sake are in the database?**
A: Currently, the database includes [NUMBER] sake from [NUMBER] breweries.

**Q: How is sake information verified?**
A: Information is sourced from brewery data and verified by sake experts.

**Q: Can I suggest sake to add?**
A: Yes! Contact us at suggestions@sakesensei.com with sake details.

## Getting the Most Out of Sake Sensei

### Beginner's Journey

1. **Week 1:** Complete preference survey, explore 3-5 recommended sake
2. **Week 2-4:** Try different sake types, record your experiences
3. **Month 2:** Notice how recommendations improve based on your history
4. **Ongoing:** Update preferences, explore new breweries, track your journey

### Sake Explorer Path

- Try one sake from each major category
- Explore different regions (Niigata, Hiroshima, Kyoto, etc.)
- Compare junmai vs. honjozo styles
- Discover seasonal sake (hiyaoroshi, shinshu, etc.)

### Food Pairing Guide

The AI can suggest pairings, but here are general guidelines:

- **Light, aromatic sake** → Sashimi, light fish
- **Rich, full-bodied sake** → Grilled meat, fried foods
- **Dry sake** → Oily fish, strong flavors
- **Sweet sake** → Desserts, fruit

## Support

### Need Help?

- **Email:** support@sakesensei.com
- **Response Time:** Within 24 hours
- **Business Hours:** Monday-Friday, 9 AM - 6 PM JST

### Report Issues

If you encounter bugs or issues:

1. Note what you were doing when the issue occurred
2. Take a screenshot if possible
3. Email details to bugs@sakesensei.com

### Feature Requests

Have ideas for new features? We'd love to hear them!

Email: features@sakesensei.com

### Community

(Future: Links to community forums, social media, etc.)

## Updates & Changelog

Check back for:
- New features
- Database updates
- Improvements to recommendations
- Bug fixes

## Glossary

Common sake terms used in the app:

- **純米酒 (Junmai-shu):** Pure rice sake (no added alcohol)
- **吟醸 (Ginjo):** Premium sake (polished to 60%)
- **大吟醸 (Daiginjo):** Super premium (polished to 50% or less)
- **本醸造 (Honjozo):** Sake with added brewer's alcohol
- **精米歩合 (Seimaibuai):** Rice polishing ratio
- **酒母 (Shubo):** Sake starter/yeast mash
- **麹 (Koji):** Rice mold used in fermentation

---

**Happy Sake Discovery! 🍶**

For more information, visit our [Operations Guide](operations.md) and [API Reference](api-reference.md).
