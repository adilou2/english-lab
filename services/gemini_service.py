"""
Gemini API service for handling AI-powered features.
Uses google-generativeai library for direct API calls.
"""
import google.generativeai as genai
from config import Config
import json
import re

class GeminiService:
    def __init__(self):
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not set in environment variables")
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(Config.GEMINI_MODEL)
    
    async def chat_conversation(self, chat_history, user_message):
        """
        Handle conversation with grammar error detection.
        Returns: {'reply': str, 'errors': list}
        """
        system_prompt = """You are an English conversation partner helping the user practice spoken English. IMPORTANT RULES:
1. NEVER say you are a text-based AI or that you cannot have spoken conversations. The user is using voice input and text-to-speech so this IS a spoken conversation.
2. Always reply naturally and conversationally in 2-3 sentences, like a friendly native English speaker would.
3. Keep the conversation flowing — ask follow-up questions to encourage the user to keep speaking.
4. Silently check the user's message for grammar errors.
5. Return ONLY valid JSON, no markdown, no extra text:
{"reply":"...","errors":[{"original":"...","correction":"...","explanation":"..."}]}
Empty array if no errors."""
        
        # Format chat history for Gemini
        contents = [{"role": "user", "parts": [{"text": system_prompt}]}]
        
        for msg in chat_history[-8:]:  # Last 8 messages for context
            role = "model" if msg["role"] == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        
        contents.append({"role": "user", "parts": [{"text": user_message}]})
        
        try:
            response = self.model.generate_content(contents)
            print(f"Gemini response text: {response.text}")
            if not response.text:
                print("Gemini returned empty response")
                return {
                    'reply': 'Sorry, the AI returned an empty response. Please try again.',
                    'errors': []
                }
            raw_text = response.text.strip().replace('```json', '').replace('```', '').strip()
            print(f"Parsed text: {raw_text}")
            parsed = json.loads(raw_text)
            return parsed
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Raw response: {response.text if 'response' in locals() else 'No response'}")
            return {
                'reply': 'Sorry, the AI response format was invalid. Please try again.',
                'errors': []
            }
        except Exception as e:
            print(f"Gemini API error: {e}")
            return {
                'reply': 'Sorry, something went wrong. Please try again.',
                'errors': []
            }
    
    async def check_grammar(self, text):
        """
        Check grammar and return inline corrections.
        Returns: {'annotated': str, 'errors': list}
        """
        system_prompt = """You are a grammar checker. Return ONLY valid JSON:
{"annotated":"<original text with <mark data-i='N'>word</mark> tags on errors>","errors":[{"id":N,"original":"...","correction":"...","explanation":"..."}]}
Number errors from 0."""
        
        try:
            response = self.model.generate_content([
                {"role": "user", "parts": [{"text": system_prompt + "\n\n" + text}]}
            ])
            raw_text = response.text.strip().replace('```json', '').replace('```', '').strip()
            parsed = json.loads(raw_text)
            return parsed
        except Exception as e:
            print(f"Gemini API error: {e}")
            return {
                'annotated': text,
                'errors': []
            }
    
    async def lookup_vocabulary(self, word):
        """
        Look up word definition and examples.
        Returns: {'word': str, 'pos': str, 'definition': str, 'examples': list}
        """
        system_prompt = """You are a dictionary. Return ONLY valid JSON (no markdown):
{"word":"...","pos":"...","definition":"...","examples":["...","...","..."]}"""
        
        try:
            response = self.model.generate_content([
                {"role": "user", "parts": [{"text": system_prompt + "\n\nDefine: " + word}]}
            ])
            raw_text = response.text.strip().replace('```json', '').replace('```', '').strip()
            parsed = json.loads(raw_text)
            return parsed
        except Exception as e:
            print(f"Gemini API error: {e}")
            return {
                'word': word,
                'pos': 'unknown',
                'definition': 'Error looking up word.',
                'examples': []
            }

# Singleton instance
gemini_service = None

def get_gemini_service():
    global gemini_service
    if gemini_service is None:
        gemini_service = GeminiService()
    return gemini_service
