import os
import httpx


class WebSearchAgent:
    description = "Handles web search queries using external search APIs (Google, Bing, etc.), returns summarized and formatted results for Slack. Supports configurable number of results."

    async def handle(self, task):
        # Debugging
        # print(task)
        query = task["payload"].get("query")
        num_results = int(task["payload"].get("num_results", 3))
        api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
        cse_id = os.getenv("GOOGLE_CSE_ID")
        MAX_RESULTS = 10  # Google Custom Search API max per request
        capped = False
        if num_results > MAX_RESULTS:
            num_results = MAX_RESULTS
            capped = True
        if not query:
            return {"report": "No search query provided.", "data": []}
        url = "https://www.googleapis.com/customsearch/v1"
        params = {"key": api_key, "cx": cse_id, "q": query, "num": num_results}
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params=params)
                data = resp.json()
            items = data.get("items", [])
            if not items:
                return {"report": "No results found.", "data": []}
            results = []
            for item in items:
                # Optionally condense snippet if too long
                snippet = item.get("snippet", "")
                if len(snippet) > 300:
                    snippet = snippet[:297] + "..."
                results.append(
                    {
                        "title": item.get("title"),
                        "link": item.get("link"),
                        "snippet": snippet,
                    }
                )
            # Format for Slack: *Title*: <URL>\nSnippet
            def format_results_for_slack(results):
                blocks = []
                for idx, item in enumerate(results, 1):
                    blocks.append(f"*{idx}. <{item['link']}|{item['title']}>*\n{item['snippet']}")
                return "\n\n".join(blocks)

            formatted = format_results_for_slack(results)
            if capped:
                formatted = f"_(Note: Only the first {MAX_RESULTS} results are shown due to API limits.)_\n\n" + formatted
            return {"report": formatted, "data": results}
        except Exception as e:
            return {"report": f"Error during web search: {e}", "data": []}
