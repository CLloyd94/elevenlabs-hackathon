# Ad Creative Optimiser Specification

This document outlines the workflow, technical architecture, and module structure for the hackathon project that creates video ads from source images. The system is implemented in Python and integrates several AI services and APIs, following an agent-based architecture pattern.

---

## 1. Overview

- **Purpose:**  
  Automatically generate engaging video ads from a user-supplied image and creative brief.  
- **Key Integrations:**  
  - **fal.ai (Kling Video API):** For automated video editing and creative manipulation.
  - **GPT-4:** For generating voiceover scripts.
  - **ElevenLabs:** For converting text scripts into high-quality voiceover audio.
  - **ffmpeg:** For integrating the generated voiceover with the video ad.

---

## 2. Agent-Based Architecture

### Big Mind Agent
- **Purpose:** High-level strategic decision making and workflow orchestration
- **Responsibilities:**
  - Interpreting user requirements
  - Coordinating between tools and small minds
  - Making high-level creative decisions
  - Managing the overall ad creation workflow

### Small Mind Agents
- **Purpose:** Specialized task execution and domain-specific processing
- **Types:**
  - **Creative Agent:** Handles artistic decisions and style guidance
  - **Technical Agent:** Manages API interactions and technical processing
  - **QA Agent:** Validates outputs and ensures quality standards

### Step 3: Voiceover Creation (Optional)
- **Initial Voiceover Setup:**  
  - The user may choose to add a voiceover.
  - The user selects a preferred voice, provides a base script, and specifies the desired length.
- **Sample Generation:**  
  - The AI generates a sample voiceover script and transcript using GPT-4.
- **User Editing & Approval:**  
  - The user edits the transcript if needed; changes update the generated voiceover.
  - Once approved, the AI can produce alternative voiceover script variations for different ad versions.

### Step 4: Final Video Assembly with ffmpeg
- **Voiceover Integration:**  
  - The approved voiceover audio (generated via ElevenLabs) is merged with the video ad.
  - ffmpeg is used to handle audio synchronization and final video export.
- **Export:**  
  - The final video ad is exported with integrated voiceover.

---

## 3. Tool Integration

### Base Tool Interface
- **Location:** `tools/base.py`
- **Purpose:** Define common interface for all tools

### Specialized Tools
- **Video Creator (`tools/video_creator.py`)**
  - Interfaces with fal.ai for video generation
  - Handles video processing and manipulation
  
- **Email Sender (`tools/email_sender.py`)**
  - Manages communication with stakeholders
  - Sends notifications and updates

---

## 4. Workflow

### Step 1: User Input & Creative Brief
- **Agent Responsible:** Big Mind
- **Tools Used:** Email Sender
- **Process:**
  - Collect image and requirements
  - Store in agent memory
  - Distribute to relevant small minds

### Step 2: Video Creation
- **Agent Responsible:** Technical Small Mind
- **Tools Used:** Video Creator
- **Process:**
  - Process image via fal.ai
  - Generate initial video draft
  - Store results in memory

### Step 3: Creative Enhancement
- **Agent Responsible:** Creative Small Mind
- **Tools Used:** Video Creator, GPT-4
- **Process:**
  - Create voiceover scripts
  - Apply creative modifications

### Step 4: Quality Assurance
- **Agent Responsible:** QA Small Mind
- **Process:**
  - Validate outputs
  - Check against requirements
  - Prepare for delivery

---

## 5. Project Structure

```
ai_cmo/
├── agents/
│   ├── Big_Mind.py
│   ├── small_mind.py
│   └── memory/
├── tools/
│   ├── base.py
│   ├── video_creator.py
│   └── email_sender.py
├── utils/
├── app/
└── tests/
```

---

## 6. Dependencies & Environment

- **Programming Language:**  
  - Python 3.x
- **Key Libraries/SDKs:**  
  - fal.ai (Kling Video API client)  
  - OpenAI GPT-4 API client  
  - ElevenLabs API client  
  - ffmpeg-python
- **Additional Libraries:**  
  - requests, json, and any others required for API integration
- **Security:**  
  - Store all API keys and sensitive credentials securely

---

## 7. Future Enhancements

- **Agent Improvements:**
  - Enhanced memory systems
  - Better inter-agent communication
  - Expanded tool integration
- **UI Improvements:**
  - Real-time editing and preview features
- **Performance Optimizations:**
  - Parallel processing of agent tasks
  - Improved memory management

---

This spec provides a comprehensive overview of the project while respecting the existing agent-based architecture. It serves as a reference document for all AI agents and developers involved, ensuring a consistent understanding of the workflow and technical requirements.
