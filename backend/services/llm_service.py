import json
import re
import httpx
from typing import Dict, Any, List, Optional
from backend.config import settings
from backend.models import AnalysisResult

# Fallback issue dictionaries
ISSUE_PATTERNS = {
    "Cleanliness": [r"filth", r"dirty", r"hair in", r"stain", r"bath", r"toilet", r"smell", r"odor", r"dust", r"mold", r"bug", r"unclean"],
    "Maintenance": [r"\bac\b", r"air condition", r"leak", r"broken", r"not work", r"faulty", r"repair", r"water pressure", r"heater", r"hot water"],
    "Staff Responsiveness": [r"no one came", r"ignored", r"called.*reception", r"called.*front desk", r"unresponsive", r"delayed response", r"attitude"],
    "Staff Attitude": [r"uninterested", r"rude", r"didn't apologize", r"did not apologize", r"unprofessional", r"scowl", r"hostile", r"careless"],
    "Check-in/out": [r"check-in", r"check in", r"check out", r"waited", r"front desk", r"reception line", r"long wait", r"delay at desk"],
    "Food Quality": [r"cold food", r"portion size", r"taste", r"bland", r"raw", r"stale", r"food was cold", r"restaurant", r"breakfast", r"spilled"],
    "Noise": [r"noise", r"construction", r"walls are paper", r"loud", r"could not sleep", r"sleepless", r"screaming", r"neighbor"],
    "Amenities": [r"gym", r"pool", r"treadmill", r"equipment", r"spa", r"elevator", r"lift", r"parking"],
    "Connectivity": [r"wifi", r"wi-fi", r"internet", r"slow connection", r"network", r"signal"],
    "Value": [r"waste of money", r"overpriced", r"laughably small", r"price", r"cost", r"too expensive", r"hidden fee", r"refund"]
}

POSITIVE_PATTERNS = [
    r"wonderful", r"superb", r"excellent", r"immaculate", r"above and beyond",
    r"loved", r"fantastic", r"great stay", r"impressed", r"highly recommend",
    r"courteous", r"peaceful", r"exceptional", r"delight", r"favorite"
]

class LLMService:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.gemini_key = settings.GEMINI_API_KEY
        self.openai_key = settings.OPENAI_API_KEY
        self.anthropic_key = settings.ANTHROPIC_API_KEY

    async def analyze_sentiment(
        self,
        text: str,
        rating: int = 3,
        guest_name: str = "Guest",
        platform: str = "Hotel Portal"
    ) -> AnalysisResult:
        """
        Analyzes the review sentiment using configured LLM API (Gemini/OpenAI/Claude)
        or falls back to an intelligent hospitality NLP heuristic engine.
        """
        # Try LLM APIs if keys are available
        if self.gemini_key and (self.provider in ("auto", "gemini")):
            try:
                res = await self._analyze_with_gemini(text, rating, guest_name)
                if res:
                    return res
            except Exception as e:
                print(f"[LLMService] Gemini error, falling back: {e}")

        if self.openai_key and (self.provider in ("auto", "openai")):
            try:
                res = await self._analyze_with_openai(text, rating, guest_name)
                if res:
                    return res
            except Exception as e:
                print(f"[LLMService] OpenAI error, falling back: {e}")

        # Intelligent NLP heuristic fallback
        return self._analyze_heuristic(text, rating, guest_name)

    async def generate_response(
        self,
        review_text: str,
        guest_name: str,
        rating: int,
        sentiment: str,
        issues: List[str],
        hotel_name: str = "The Grand ClearVision",
        tone: str = "empathetic_luxury"
    ) -> Dict[str, str]:
        """
        Generates a 5-stage personalized hospitality repair/recovery response.
        """
        if self.gemini_key and (self.provider in ("auto", "gemini")):
            try:
                resp = await self._generate_response_gemini(review_text, guest_name, rating, sentiment, issues, hotel_name)
                if resp:
                    return resp
            except Exception as e:
                print(f"[LLMService] Gemini response generation error: {e}")

        if self.openai_key and (self.provider in ("auto", "openai")):
            try:
                resp = await self._generate_response_openai(review_text, guest_name, rating, sentiment, issues, hotel_name)
                if resp:
                    return resp
            except Exception as e:
                print(f"[LLMService] OpenAI response generation error: {e}")

        # Intelligent heuristic hospitality response generator
        return self._generate_response_heuristic(review_text, guest_name, rating, sentiment, issues, hotel_name)

    def _analyze_heuristic(self, text: str, rating: int, guest_name: str) -> AnalysisResult:
        lower_text = text.lower()
        extracted_issues = []

        for category, patterns in ISSUE_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, lower_text):
                    if category not in extracted_issues:
                        extracted_issues.append(category)
                    break

        # Calculate sentiment score (0-100)
        pos_matches = sum(1 for p in POSITIVE_PATTERNS if re.search(p, lower_text))
        neg_matches = len(extracted_issues)

        if rating >= 4:
            score = min(100, 75 + (rating - 4) * 15 + pos_matches * 5)
            sentiment = "positive"
            churn_risk = max(5, 20 - rating * 3)
            urgency = "low"
        elif rating == 3:
            score = max(35, min(65, 50 + pos_matches * 5 - neg_matches * 8))
            sentiment = "neutral"
            churn_risk = 45 + neg_matches * 5
            urgency = "normal"
        else: # 1 or 2 stars
            score = max(5, int(rating * 12 - neg_matches * 4))
            sentiment = "negative"
            churn_risk = min(98, 70 + (3 - rating) * 12 + neg_matches * 3)
            urgency = "critical" if rating == 1 or churn_risk > 85 else "high"

        # Department mapping
        department = "Front Office"
        if any(i in ["Cleanliness", "Maintenance"] for i in extracted_issues):
            department = "Housekeeping & Engineering"
        elif any(i in ["Food Quality"] for i in extracted_issues):
            department = "Food & Beverage"
        elif any(i in ["Noise"] for i in extracted_issues):
            department = "Guest Relations"

        return AnalysisResult(
            sentiment=sentiment,
            score=score,
            issues=extracted_issues,
            churn_risk_score=churn_risk,
            urgency=urgency,
            root_cause=f"Identified {len(extracted_issues)} pain point(s): {', '.join(extracted_issues)}" if extracted_issues else "General experience feedback",
            department=department
        )

    def _generate_response_heuristic(
        self,
        review_text: str,
        guest_name: str,
        rating: int,
        sentiment: str,
        issues: List[str],
        hotel_name: str
    ) -> Dict[str, str]:
        first_name = guest_name.split()[0] if guest_name else "Valued Guest"
        issues_str = ", ".join(issues).lower() if issues else "details of your stay"

        if rating >= 4:
            resp_type = "VIP Delight & Loyalty Reinforcement"
            response = (
                f"Dear {first_name},\n\n"
                f"Thank you so much for your glowing {rating}-star review of {hotel_name}! "
                f"It brings immense joy to our entire team to know that you had such a wonderful experience. "
                f"Your generous praise has been shared with our front line and concierge teams who take great pride in delivering memorable moments. "
                f"We look forward to welcoming you back for another exceptional stay in the near future.\n\n"
                f"Warmest regards,\nGuest Experience Team\n{hotel_name}"
            )
        elif rating == 3:
            resp_type = "Proactive Service Calibration"
            response = (
                f"Dear {first_name},\n\n"
                f"Thank you for sharing your constructive feedback regarding your recent stay at {hotel_name}. "
                f"While we are pleased you appreciated our property, we regret that aspects of {issues_str} did not completely exceed your expectations. "
                f"We take every observation to heart, and our management team is currently reviewing improvements for the areas you mentioned. "
                f"We would love the privilege of welcoming you back for a truly flawless 5-star experience next time.\n\n"
                f"Sincerely,\nGuest Relations Management\n{hotel_name}"
            )
        else: # 1 or 2 stars
            resp_type = "Manager Escalation & Sentiment Repair"
            compensation = "a complimentary upgraded stay on us along with a full dining credit" if rating == 1 else "a 25% courtesy discount on your next visit and an executive suite upgrade"
            response = (
                f"Dear {first_name},\n\n"
                f"Please accept our deepest apologies for the unacceptable experience you encountered during your time at {hotel_name}. "
                f"The shortcomings you described regarding {issues_str} fall far beneath the exacting standards of luxury hospitality we pride ourselves upon.\n\n"
                f"We have escalated your feedback directly to our General Manager and relevant department heads for immediate corrective action. "
                f"To begin making amends, we would be honored to extend {compensation}. "
                f"Our Guest Relations Director will reach out to you personally to ensure your concerns are rectified fully.\n\n"
                f"With sincere regret and dedication to your satisfaction,\n"
                f"Office of the General Manager\n{hotel_name}"
            )

        return {"response": response, "response_type": resp_type}

    async def _analyze_with_gemini(self, text: str, rating: int, guest_name: str) -> Optional[AnalysisResult]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.LLM_MODEL}:generateContent?key={self.gemini_key}"
        prompt = (
            f"Analyze this hotel review for hospitality sentiment repair:\n"
            f"Guest: {guest_name}, Rating: {rating} stars\n"
            f"Review: \"{text}\"\n\n"
            f"Return ONLY valid JSON with keys:\n"
            f"- sentiment: 'positive', 'neutral', or 'negative'\n"
            f"- score: integer from 0 to 100\n"
            f"- issues: array of strings from ['Cleanliness', 'Maintenance', 'Staff Service', 'Check-in/out', 'Food & Dining', 'Amenities', 'Noise/Comfort', 'Value']\n"
            f"- churn_risk_score: integer 0 to 100\n"
            f"- urgency: 'low', 'normal', 'high', or 'critical'\n"
            f"- department: most relevant department\n"
            f"- root_cause: concise summary of the primary failure point"
        )
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                clean_json = re.search(r"\{.*\}", raw_text, re.DOTALL)
                if clean_json:
                    parsed = json.loads(clean_json.group(0))
                    return AnalysisResult(
                        sentiment=parsed.get("sentiment", "neutral"),
                        score=int(parsed.get("score", 50)),
                        issues=parsed.get("issues", []),
                        churn_risk_score=int(parsed.get("churn_risk_score", 50)),
                        urgency=parsed.get("urgency", "normal"),
                        department=parsed.get("department", "Front Office"),
                        root_cause=parsed.get("root_cause", "")
                    )
        return None

    async def _analyze_with_openai(self, text: str, rating: int, guest_name: str) -> Optional[AnalysisResult]:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.openai_key}", "Content-Type": "application/json"}
        prompt = (
            f"Analyze this hotel guest review:\nReview: \"{text}\"\nRating: {rating} stars. Guest: {guest_name}.\n"
            f"Output JSON with keys: sentiment (positive/neutral/negative), score (0-100), "
            f"issues (list), churn_risk_score (0-100), urgency (low/normal/high/critical), department, root_cause."
        )
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"}
        }
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                parsed = json.loads(data["choices"][0]["message"]["content"])
                return AnalysisResult(
                    sentiment=parsed.get("sentiment", "neutral"),
                    score=int(parsed.get("score", 50)),
                    issues=parsed.get("issues", []),
                    churn_risk_score=int(parsed.get("churn_risk_score", 50)),
                    urgency=parsed.get("urgency", "normal"),
                    department=parsed.get("department", "Front Office"),
                    root_cause=parsed.get("root_cause", "")
                )
        return None

    async def _generate_response_gemini(self, review_text: str, guest_name: str, rating: int, sentiment: str, issues: List[str], hotel_name: str) -> Optional[Dict[str, str]]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.LLM_MODEL}:generateContent?key={self.gemini_key}"
        prompt = (
            f"You are the General Manager of luxury hotel '{hotel_name}'. "
            f"Draft an elite 5-stage personalized service recovery response to this guest review:\n"
            f"Guest: {guest_name}, Rating: {rating}★, Sentiment: {sentiment}, Issues: {', '.join(issues)}.\n"
            f"Review: \"{review_text}\"\n\n"
            f"Return JSON with:\n"
            f"- response_type: category title (e.g. 'Manager Escalation & Service Recovery')\n"
            f"- response: the full drafted reply text"
        )
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                clean_json = re.search(r"\{.*\}", raw_text, re.DOTALL)
                if clean_json:
                    parsed = json.loads(clean_json.group(0))
                    return {"response": parsed.get("response", ""), "response_type": parsed.get("response_type", "AI Recovery")}
        return None

    async def _generate_response_openai(self, review_text: str, guest_name: str, rating: int, sentiment: str, issues: List[str], hotel_name: str) -> Optional[Dict[str, str]]:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.openai_key}", "Content-Type": "application/json"}
        prompt = (
            f"Write a luxury hospitality response from the General Manager of '{hotel_name}' to:\n"
            f"Guest: {guest_name} ({rating} stars). Issues: {', '.join(issues)}.\nText: \"{review_text}\".\n"
            f"Return JSON with 'response_type' and 'response'."
        )
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"}
        }
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                parsed = json.loads(data["choices"][0]["message"]["content"])
                return {"response": parsed.get("response", ""), "response_type": parsed.get("response_type", "AI Recovery")}
        return None

llm_service = LLMService()
