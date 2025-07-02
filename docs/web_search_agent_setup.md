# Web Search Agent: Start-to-Finish Implementation Guide

This guide covers the full lifecycle of building, integrating, and configuring the Web Search Agent for Zia-AI, including API integration, query handling, Slack formatting, and result configuration.

---

## 1. Integrate with Search APIs (Google, Bing, etc.)

### 1.1. Choose and Register for Search APIs
- **Google Custom Search API:**
  - Go to [Google Custom Search JSON API](https://developers.google.com/custom-search/v1/overview).
  - Create a Google Cloud project and enable the Custom Search API.
  - Set up a Custom Search Engine (CSE) and get your API key and CSE ID.
- **Bing Web Search API:**
  - Go to [Microsoft Azure Portal](https://portal.azure.com/).
  - Create a Bing Search v7 resource.
  - Obtain your API key from the Azure portal.

### 1.2. Add API Keys to Environment
Add the following to your `.env` file:
```env
GOOGLE_SEARCH_API_KEY=your_google_api_key
GOOGLE_CSE_ID=your_cse_id
BING_SEARCH_API_KEY=your_bing_api_key
```

### 1.3. Install Required Python Packages
Add to `requirements.txt` (if not already present):
```txt
httpx
```
Install with:
```sh
pip install httpx
```

### 1.4. Implement API Client Logic
In `agents/web_search_agent.py`, implement async methods to call Google and/or Bing APIs.
Example (Google):
```python
import os
import httpx

class WebSearchAgent:
    async def handle(self, task):
        query = task['payload'].get('query')
        num_results = int(task['payload'].get('num_results', 3))
        api_key = os.getenv('GOOGLE_SEARCH_API_KEY')
        cse_id = os.getenv('GOOGLE_CSE_ID')
        if not query:
            return {'report': 'No search query provided.'}
        url = 'https://www.googleapis.com/customsearch/v1'
        params = {'key': api_key, 'cx': cse_id, 'q': query, 'num': num_results}
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params=params)
                data = resp.json()
            items = data.get('items', [])
            if not items:
                return {'report': 'No results found.'}
            results = []
            for item in items:
                results.append({
                    'title': item.get('title'),
                    'link': item.get('link'),
                    'snippet': item.get('snippet')
                })
            def format_results_for_slack(results):
                blocks = []
                for idx, item in enumerate(results, 1):
                    blocks.append(f"*{idx}. <{item['link']}|{item['title']}>*\n{item['snippet']}")
                return '\n\n'.join(blocks)
            return {'report': format_results_for_slack(results)}
        except Exception as e:
            return {'report': f'Error during web search: {e}'}
```

---

## 2. Implement Search Query Handler

### 2.1. Define the Query Schema
The agent should expect a task dictionary with at least:
```json
{
    "type": "web_search",
    "payload": {
        "query": "your search terms",
        "num_results": 3  // Optional, default to 3
    },
    "user": "...",
    "context": {...}
}
```

### 2.2. Validate and Preprocess the Query
- Ensure the query is present and not empty.
- Set a default for `num_results` if not provided (e.g., 3).

### 2.3. Call the Search API
- Use the async client to call the search API with the query and number of results.
- Handle API errors gracefully (e.g., invalid key, quota exceeded, no results).

---

## 3. Summarize and Format Results for Slack

### 3.1. Parse API Response
- Extract relevant fields from the API response (e.g., title, snippet, link for each result).

### 3.2. Summarize Results
- Optionally, use Gemini LLM or a simple summarizer to condense snippets if needed.
- For each result, create a summary string:
  ```
  *Title*: <URL>
  Snippet
  ```

### 3.3. Format for Slack
- Use Slack's Markdown formatting for clarity.
- Example:
  ```python
  def format_results_for_slack(results):
      blocks = []
      for idx, item in enumerate(results, 1):
          title = item.get('title')
          link = item.get('link')
          snippet = item.get('snippet')
          blocks.append(f"*{idx}. <{link}|{title}>*\n{snippet}")
      return '\n\n'.join(blocks)
  # ...
  return {"report": format_results_for_slack(results)}
  ```

---

## 4. Make Number of Results Configurable

### 4.1. Accept `num_results` in Payload
- In the `handle` method, read `num_results` from the task payload.
- Validate that it is an integer and within API limits (e.g., 1–10 for Google).

### 4.2. Document Usage for Users
- In user documentation and Slack help, explain how to specify the number of results:
  ```
  /zia search "python async" 5
  ```
  or
  "Search for top 5 articles on Python async"

### 4.3. Fallback and Error Handling
- If the user requests more than the API allows, cap to the maximum and notify the user in the response.

---

## 5. Testing and Validation

### 5.1. Unit Tests
- Write tests for:
  - Query parsing and validation
  - API call logic (mocked)
  - Slack formatting

### 5.2. Integration Tests
- Test the full flow via the orchestrator and Slack interface.

### 5.3. Error Handling
- Simulate API failures, empty results, and invalid queries to ensure graceful degradation.

---

## 6. Deployment and Monitoring

### 6.1. Logging
- Log all queries, API responses (truncated), and errors for monitoring and debugging.

### 6.2. Monitoring
- Track API usage and error rates.
- Set up alerts for quota exhaustion or repeated failures.

---

## 7. Example: Complete WebSearchAgent Implementation

```python
import os
import httpx

class WebSearchAgent:
    async def handle(self, task):
        query = task['payload'].get('query')
        num_results = int(task['payload'].get('num_results', 3))
        api_key = os.getenv('GOOGLE_SEARCH_API_KEY')
        cse_id = os.getenv('GOOGLE_CSE_ID')
        if not query:
            return {'report': 'No search query provided.'}
        url = 'https://www.googleapis.com/customsearch/v1'
        params = {'key': api_key, 'cx': cse_id, 'q': query, 'num': num_results}
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params=params)
                data = resp.json()
            items = data.get('items', [])
            if not items:
                return {'report': 'No results found.'}
            results = []
            for item in items:
                results.append({
                    'title': item.get('title'),
                    'link': item.get('link'),
                    'snippet': item.get('snippet')
                })
            def format_results_for_slack(results):
                blocks = []
                for idx, item in enumerate(results, 1):
                    blocks.append(f"*{idx}. <{item['link']}|{item['title']}>*\n{item['snippet']}")
                return '\n\n'.join(blocks)
            return {'report': format_results_for_slack(results)}
        except Exception as e:
            return {'report': f'Error during web search: {e}'}
```

---

## 8. Final Checklist

- [x] API keys securely stored and loaded from environment
- [x] Async API calls implemented
- [x] Query handler validates and parses input
- [x] Results summarized and formatted for Slack
- [x] Number of results is user-configurable
- [x] Errors and edge cases handled gracefully
- [x] Logging and monitoring in place

---

**End of Web Search Agent Implementation Guide**


