# AI_Offer_Letter_Agent

# Offer_Letter_AI_Agent

This project is an automated offer letter generation system that harnesses AI and predefined templates to create professional offer letters based on employee data. It includes a FastAPI backend, a React frontend, and ntegrates with OpenRouter.ai for AI-driven content generation with a fallback to template-based generation.

## Project Overview

### Purpose
Generate customized offer letters of employees using data from Employee_List.csv and company policies stored in HR Leave Policy.pdf and HR Travel Policy.pdf.
### Frontend
React-based single-page application for user interaction.
### Backend 
FastAPI server with Python-based logic for offer letter generation.
### AI Integration
Utilizes OpenRouter.ai via Langchain for dynamic content generation, with a robust fallback to templates.

## Prerequisites
Python: Version 3.8.10.
Node.js: Version 18.x or later (frontend).
npm: Included with Node.js.
Git: For cloning the repository.

## Tools Used
### Backend (Python Libraries):
fastapi: For building the API server.

langchain: For integrating AI models and managing prompts.

langchain_openai: Interface with OpenRouter.ai LLM.

pandas: For handling CSV data.

dotenv: For managing environment variables.

uvicorn: ASGI server for running FastAPI.

### Frontend:
react: For building the UI.
tailwindcss: For styling the React app.

### Other Tools:
virtualenv: For creating isolated python env.
npm: For managing frontend dependencies.

## Installation Process:
1.) Clone the Repository 

2.) Set up the virtual env. by using "python3.8 -m venv .venv" and activate it by ".venv\Scripts\activate" commands on windows.

3.) Use "pip install -r requirements.txt" command to install Python dependencies.

4.) Create a .env file in the project root directory and add API keys for Pinecone and OpenRouter.ai 

5.) Use "npm install" to install frontend dependencies.

6.) Check all the given files in data folder.

7.) Start both the backend and frontend server by using "cd ../backend
uvicorn main:app --reload --host 127.0.0.1 --port 8000" and "cd frontend
npm run dev" commands respectively. 

8.) Open the browser and visit "http://localhost:5173" to use the application.

## Usage
Enter an employee name in the input field (must match a name in Employee_List.csv).

Click "Generate Offer Letter" to fetch and display the offer letter.

Use the "Back to Search" button to return to the input page.

If an error occurs (e.g., name not found), it will be displayed on the screen.
