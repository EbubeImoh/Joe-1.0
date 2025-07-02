class LLMResponseAgent:
    description = "Directly answers user queries using the Gemini LLM for conversational or general-purpose responses."

    def __init__(self, gemini_model):
        self.gemini_model = gemini_model

    async def handle(self, task):
        prompt = task.get("payload", {}).get("query", "")
        if not prompt:
            return {"report": "No input provided.", "data": []}
        if not self.gemini_model:
            return {"report": "LLM is not available.", "data": []}
        response = await self.gemini_model.generate_content_async(prompt)
        return {"report": getattr(response, "text", ""), "data": []}
