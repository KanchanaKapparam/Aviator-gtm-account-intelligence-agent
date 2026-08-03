import os
import json
import csv
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv
import requests
from duckduckgo_search import DDGS
from google import genai
from google.genai import types
from jinja2 import Environment, FileSystemLoader

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(override=True)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class GitHubClient:
    """Helper client to fetch public organization signals from GitHub API."""
    def __init__(self, token: str = None):
        self.session = requests.Session()
        self.headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "Aviator-GTM-Research-Agent/1.0"
        }
        if token:
            self.headers["Authorization"] = f"token {token}"
            logger.info("GitHub client initialized with authorization token.")
        else:
            logger.warning("GitHub client initialized without token. Rate limits will be low (60 requests/hour).")
        self.session.headers.update(self.headers)

    def fetch_org_stats(self, org_name: str) -> Dict[str, Any]:
        """Fetches general organization information and top repository signals."""
        stats = {
            "exists": False,
            "name": org_name,
            "description": "",
            "public_repos": 0,
            "followers": 0,
            "top_languages": [],
            "recent_activity_repos": []
        }
        
        # Get general org info
        url = f"https://api.github.com/orgs/{org_name}"
        try:
            res = self.session.get(url)
            if res.status_code == 404:
                logger.warning(f"GitHub Org '{org_name}' not found.")
                return stats
            res.raise_for_status()
            data = res.json()
            stats["exists"] = True
            stats["name"] = data.get("name") or org_name
            stats["description"] = data.get("description") or ""
            stats["public_repos"] = data.get("public_repos", 0)
            stats["followers"] = data.get("followers", 0)
        except Exception as e:
            logger.error(f"Error fetching org details for {org_name}: {e}")
            return stats

        # Get top repositories to extract languages and recent activity
        repos_url = f"https://api.github.com/orgs/{org_name}/repos"
        try:
            params = {"sort": "pushed", "per_page": 20}
            res = self.session.get(repos_url, params=params)
            res.raise_for_status()
            repos = res.json()
            
            languages = {}
            active_repos = []
            for repo in repos:
                if not repo.get("fork"):
                    lang = repo.get("language")
                    if lang:
                        languages[lang] = languages.get(lang, 0) + 1
                    
                    active_repos.append({
                        "name": repo.get("name"),
                        "stars": repo.get("stargazers_count", 0),
                        "description": repo.get("description") or "",
                        "pushed_at": repo.get("pushed_at")
                    })
            
            # Sort languages by frequency
            sorted_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)
            stats["top_languages"] = [lang[0] for lang in sorted_langs[:5]]
            stats["recent_activity_repos"] = active_repos[:5]
            
        except Exception as e:
            logger.error(f"Error fetching repos for {org_name}: {e}")
            
        return stats

class SearchEnricher:
    """Helper client using DuckDuckGo to find job postings and blog posts."""
    def __init__(self):
        self.ddgs = DDGS()

    def search_engineering_blog(self, company_name: str, domain: str) -> List[Dict[str, str]]:
        """Searches for DevEx, monorepos, CI/CD, or build challenges on the company engineering blog."""
        query = f"site:engineering.{domain} OR site:{domain}/blog (CI/CD OR monorepo OR merge OR testing OR build)"
        logger.info(f"Searching engineering blogs for {company_name} with query: {query}")
        results = []
        try:
            # Fetch search results
            search_results = self.ddgs.text(query, max_results=5)
            for r in search_results:
                results.append({
                    "title": r.get("title", ""),
                    "href": r.get("href", ""),
                    "body": r.get("body", "")
                })
        except Exception as e:
            logger.error(f"Error searching engineering blog for {company_name}: {e}")
        return results

    def search_jobs(self, company_name: str) -> List[Dict[str, str]]:
        """Searches for open jobs matching Developer Experience or Platform Engineering."""
        query = f'"{company_name}" ("developer experience" OR "platform engineer" OR "devops" OR "infrastructure") jobs'
        logger.info(f"Searching jobs for {company_name} with query: {query}")
        results = []
        try:
            search_results = self.ddgs.text(query, max_results=3)
            for r in search_results:
                results.append({
                    "title": r.get("title", ""),
                    "href": r.get("href", ""),
                    "body": r.get("body", "")
                })
        except Exception as e:
            logger.error(f"Error searching jobs for {company_name}: {e}")
        return results

class OutreachGenerator:
    """Uses Gemini API to synthesize technical context and generate highly personalized outreach emails."""
    def __init__(self, api_key: str):
        if not api_key or api_key == "your_gemini_api_key_here":
            raise ValueError("A valid GEMINI_API_KEY must be provided in the environment or .env file.")
        # Initialize Google GenAI client
        self.client = genai.Client(api_key=api_key)

    def generate_gtm_intelligence(self, company_name: str, git_stats: Dict[str, Any], blog_insights: List[Dict[str, str]], job_insights: List[Dict[str, str]]) -> Dict[str, Any]:
        """Prompts Gemini to evaluate fit and write personalized copy."""
        
        # Prepare context summaries for LLM prompt
        github_summary = (
            f"Organization Name: {git_stats.get('name')}\n"
            f"Description: {git_stats.get('description')}\n"
            f"Public Repositories: {git_stats.get('public_repos')}\n"
            f"Top Languages: {', '.join(git_stats.get('top_languages', []))}\n"
            f"Active public repos sample:\n"
        )
        for repo in git_stats.get('recent_activity_repos', []):
            github_summary += f" - {repo['name']} ({repo['stars']} stars, {repo['description']})\n"

        blog_summary = ""
        if blog_insights:
            for i, blog in enumerate(blog_insights, 1):
                blog_summary += f"[{i}] {blog['title']} ({blog['href']})\nSnippet: {blog['body']}\n\n"
        else:
            blog_summary = "No relevant engineering blog posts found."

        job_summary = ""
        if job_insights:
            for i, job in enumerate(job_insights, 1):
                job_summary += f"[{i}] {job['title']} ({job['href']})\nSnippet: {job['body']}\n\n"
        else:
            job_summary = "No active Developer Experience / Infrastructure jobs found."

        # Construct prompt
        prompt = f"""
You are an expert Go-To-Market (GTM) Engineer at Aviator.
Aviator builds modern developer workflow automation tools:
- **MergeQueue**: Automatically coordinates pre-merge tests and runs queue verification to prevent broken builds and merge conflicts. Essential for teams with active codebases/monorepos.
- **FlexReview**: Intelligently and contextually routes pull request reviews to the right developers to speed up approvals.
- **Runbooks**: Collaborative AI agent platform that lets developer experience (DevEx) and infrastructure teams automate complex scripts and release workflows using plain English specs.

We sell to Developer Experience (DevEx) Leads, Platform Engineers, and Engineering Directors. They hate generic, templated outbound sales emails and respect engineers who understand their architecture and pain points.

Use the technical context below to analyze {company_name}.

--- TECHNICAL CONTEXT FOR {company_name} ---
[GitHub Signals]
{github_summary}

[Engineering Blog & Web Mentions]
{blog_summary}

[Active Job Openings]
{job_summary}
---------------------------------------------

YOUR TASK:
1. Provide a "fit_score" (High, Medium, or Low).
   - High: High public PR activity/repos, heavy JS/TS/Go/Rust codebases, active platform hiring, or engineering blog posts mentioning CI/CD scaling or test flakiness.
   - Medium: Moderate activity, typical stack, no direct DevEx mentions.
   - Low: Low public presence, tiny tech footprint, or outdated stack.
2. Provide a 2-3 sentence "fit_reasoning" explaining exactly why they would care about Aviator.
3. Draft a "personalized_email" from you (a GTM Engineer at Aviator) to a DevEx lead at {company_name}.
   - Address them in a professional but casual tone (like one engineer to another).
   - Mention specific, real details from their tech stack (like their use of {', '.join(git_stats.get('top_languages', []))}) and reference a specific search signal (like their active job post or a specific blog post title if available).
   - Show how Aviator's tools (MergeQueue, FlexReview, or Runbooks) can solve a concrete bottleneck they are likely experiencing (e.g. merge conflicts, long CI queues, review lag).
   - Keep it concise (under 150 words). Make the call to action low friction (e.g., checking if their team runs into merge queue issues, or sharing a quick DevEx benchmark).

Provide your response in JSON format. Use the following structure:
{{
  "fit_score": "High" | "Medium" | "Low",
  "fit_reasoning": "Reason here...",
  "personalized_email": "Subject: ...\\n\\nBody: ..."
}}
Do NOT include any markdown code blocks (like ```json) in your final response. Return ONLY raw JSON content.
"""
        try:
            logger.info(f"Generating GTM intelligence for {company_name} using Gemini API...")
            response = self.client.models.generate_content(
                model='gemini-3.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            # Parse the response text
            result = json.loads(response.text.strip())
            return result
        except Exception as e:
            logger.error(f"Error generating GTM intelligence: {e}")
            return {
                "fit_score": "Medium",
                "fit_reasoning": "Failed to generate fit analysis due to an error.",
                "personalized_email": f"Subject: Developer workflows at {company_name}\n\nHi,\n\nI was looking at {company_name}'s GitHub repositories and wanted to check how you manage merge coordination and DevEx."
            }

def run_research():
    # Load input companies
    companies_file = "companies.json"
    if not os.path.exists(companies_file):
        logger.error(f"Input file {companies_file} not found. Please create it.")
        return

    with open(companies_file, "r") as f:
        companies = json.load(f)

    # Initialize clients
    github_client = GitHubClient(token=GITHUB_TOKEN)
    search_enricher = SearchEnricher()
    
    try:
        outreach_gen = OutreachGenerator(api_key=GEMINI_API_KEY)
    except Exception as e:
        logger.error(f"Initialization error: {e}")
        print("\n[ERROR] Gemini API Key is missing or invalid.")
        print("Please copy '.env.example' to '.env' and fill in your GEMINI_API_KEY.")
        print("Get a free key from: https://aistudio.google.com/app/apikey\n")
        return

    leads_data = []

    for idx, company in enumerate(companies, 1):
        name = company.get("name")
        domain = company.get("domain")
        github_org = company.get("github_org")
        
        logger.info(f"[{idx}/{len(companies)}] Starting research for {name} ({domain})...")
        
        # 1. Gather GitHub Signals
        git_stats = github_client.fetch_org_stats(github_org)
        
        # 2. Gather Web Search Signals
        blog_results = search_enricher.search_engineering_blog(name, domain)
        job_results = search_enricher.search_jobs(name)
        
        # 3. Generate AI insights & Outreach
        insights = outreach_gen.generate_gtm_intelligence(
            company_name=name,
            git_stats=git_stats,
            blog_insights=blog_results,
            job_insights=job_results
        )
        
        # Compile record
        lead = {
            "name": name,
            "domain": domain,
            "github_org": github_org,
            "public_repos": git_stats.get("public_repos", 0),
            "top_languages": ", ".join(git_stats.get("top_languages", [])),
            "fit_score": insights.get("fit_score", "Medium"),
            "fit_reasoning": insights.get("fit_reasoning", ""),
            "personalized_email": insights.get("personalized_email", ""),
            "scraped_blogs": blog_results,
            "scraped_jobs": job_results
        }
        leads_data.append(lead)

    # Save to CSV
    csv_file = "outreach_leads.csv"
    try:
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "name", "domain", "github_org", "public_repos", "top_languages", "fit_score", "fit_reasoning", "personalized_email"
            ])
            writer.writeheader()
            for lead in leads_data:
                writer.writerow({
                    "name": lead["name"],
                    "domain": lead["domain"],
                    "github_org": lead["github_org"],
                    "public_repos": lead["public_repos"],
                    "top_languages": lead["top_languages"],
                    "fit_score": lead["fit_score"],
                    "fit_reasoning": lead["fit_reasoning"],
                    "personalized_email": lead["personalized_email"]
                })
        logger.info(f"Saved {len(leads_data)} leads to {csv_file}")
    except Exception as e:
        logger.error(f"Error writing CSV file: {e}")

    # Generate HTML report
    try:
        # Create templates directory if it doesn't exist
        os.makedirs("templates", exist_ok=True)
        
        # Check if template exists
        template_path = "templates/report_template.html"
        if os.path.exists(template_path):
            env = Environment(loader=FileSystemLoader("."))
            template = env.get_template(template_path)
            html_output = template.render(leads=leads_data)
            
            with open("report.html", "w", encoding="utf-8") as f:
                f.write(html_output)
            logger.info("Successfully generated interactive HTML report: report.html")
        else:
            logger.warning("HTML template templates/report_template.html not found. Skipping HTML report generation.")
    except Exception as e:
        logger.error(f"Error compiling HTML report: {e}")

if __name__ == "__main__":
    run_research()
