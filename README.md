# Marketing Employee

An AI-powered system to generate video ads from images, integrate with Meta Ads, and provide real-time performance insights. Marketing Employee automates repetitive tasks so marketers can focus on strategy rather than creative bottlenecks and data wrangling.

---

## Table of Contents
1. [Features](#features)
2. [How It Works](#how-it-works)
3. [How to Use](#how-to-use)
4. [Future Plans](#future-plans)

---

## Features
1. **Creative Generation**  
   - Converts static images into full-fledged video ads.  
   - Automatically adds voiceovers and subtitles for professional polish.

2. **Meta Ads Integration**  
   - Uploads finalized video ads directly to Meta Ads.  
   - Retrieves performance data, reducing manual work.

3. **Live Data Analysis**  
   - Pulls real-time performance metrics from Meta Ads.  
   - Answers your questions via voice or text for instant insights and optimization tips.

---

## How It Works

**1. AI Processing Layers**  
- **"Small Brain"**: Manages user requests for low-latency responses (routing, basic instructions).  
- **"Big Brain"**: Specialized modules for tasks like creative generation and data retrieval. These modules use advanced tools (e.g., image processing, text-to-speech) to fulfill complex requests.

**2. Video Creation Pipeline**  
- **Image Processing**: Takes your static assets (images) and converts them to video.  
- **Text-to-Speech + Subtitles**: Generates a voiceover script, then aligns subtitles to spoken words for a seamless viewing experience.

**3. Meta Ads API Integration**  
- **Uploading**: Once the video is rendered, it’s automatically pushed to your Meta Ads account.  
- **Insights**: Pulls performance metrics (CTR, conversions, view-through rates, etc.) and funnels this data into the AI for real-time analysis.

**4. Conversational Interface**  
- **Voice or Text**: You can chat with the AI to dive deeper into performance data or request new variations of your ads.  
- **Optimization Advice**: The AI uses the metrics it retrieves to suggest creative tweaks or campaign improvements.

---

## How to Use
Start Chat inferface with: streamlit run app/main.py

1. **Prepare Your Media**  
   - Collect the images or creative assets you want to turn into video ads.  
   - Have a voiceover script ready if you want custom text-to-speech (otherwise, the AI can generate one).

2. **Sign In to Marketing Employee**  
   - Provide your Meta Ads credentials so the system can upload ads and access performance data on your behalf.

3. **Generate Video Ads**  
   - In the interface, upload your images and input any text or script you’d like for the voiceover.  
   - Click _Generate_ to trigger the AI’s video pipeline.

4. **Review & Submit**  
   - Watch the generated preview, confirm subtitles are aligned, and approve the final video.  
   - Once approved, hit _Upload_ to push your new ad to your Meta Ads account.

5. **Monitor Performance**  
   - Ask the AI about ongoing campaign metrics (e.g., “How is my new video performing?”).  
   - Get immediate feedback and suggestions for optimization.

---

## Future Plans
- **More Platforms**: Extend support beyond Meta Ads to TikTok, YouTube, and other major advertising platforms.  
- **Advanced Editing Tools**: Offer a more sophisticated video editor for granular tweaks (e.g., cutting scenes, adding graphics).  
- **Ad-Level Insights**: Use performance data (view-through rates, conversions) to automatically recommend new creative angles and variations.  
- **Batch Processing**: Handle multiple video ads at once for power users and agencies.  
- **Refined Subtitle Syncing**: Enhance voice-subtitle alignment to ensure perfect text timing.  

---

Have questions or ideas? Submit an issue or pull request! We’re excited to improve Marketing Employee with the help of the community.
