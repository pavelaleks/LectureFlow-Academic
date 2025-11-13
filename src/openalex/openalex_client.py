"""
OpenAlex API client for scholarly literature search.
"""
import requests
from typing import List, Dict, Optional
import config


class OpenAlexClient:
    """Client for interacting with OpenAlex API."""
    
    def __init__(self):
        """Initialize OpenAlex client."""
        self.base_url = config.OPENALEX_BASE_URL
        self.email = config.OPENALEX_EMAIL
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make HTTP request to OpenAlex API."""
        url = f"{self.base_url}/{endpoint}"
        headers = {}
        
        if self.email:
            params = params or {}
            params['mailto'] = self.email
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"OpenAlex API error: {str(e)}")
    
    def search_works(
        self,
        query: str,
        per_page: int = 25,
        sort: str = "relevance_score:desc"
    ) -> List[Dict]:
        """
        Search for works in OpenAlex.
        
        Args:
            query: Search query
            per_page: Number of results per page
            sort: Sort order
        
        Returns:
            List of work dictionaries
        """
        params = {
            "search": query,
            "per_page": per_page,
            "sort": sort
        }
        
        result = self._make_request("works", params)
        return result.get("results", [])
    
    def build_bibliography(
        self,
        works: List[Dict]
    ) -> List[Dict]:
        """
        Build bibliography entries from OpenAlex works.
        
        Args:
            works: List of work dictionaries from OpenAlex
        
        Returns:
            List of formatted bibliography entries
        """
        bibliography = []
        
        for work in works:
            # Extract authors
            authors = []
            if work.get("authorships"):
                for authorship in work["authorships"]:
                    author = authorship.get("author", {})
                    display_name = author.get("display_name", "Unknown")
                    authors.append(display_name)
            
            # Extract year
            publication_date = work.get("publication_date", "")
            year = publication_date.split("-")[0] if publication_date else "Unknown"
            
            # Extract DOI
            doi = work.get("doi", "")
            if doi:
                doi = doi.replace("https://doi.org/", "")
            
            # Extract OpenAlex ID
            openalex_id = work.get("id", "").replace("https://openalex.org/", "")
            
            # Extract source (journal/venue)
            source = "Unknown"
            if work.get("primary_location", {}).get("source", {}):
                source = work["primary_location"]["source"].get("display_name", "Unknown")
            elif work.get("locations"):
                for loc in work["locations"]:
                    if loc.get("source", {}).get("display_name"):
                        source = loc["source"]["display_name"]
                        break
            
            entry = {
                "title": work.get("title", "Untitled"),
                "authors": authors[:5],  # Limit to first 5 authors
                "year": year,
                "doi": doi,
                "openalex_id": openalex_id,
                "source": source,
                "summary": "To be summarized by LLM"
            }
            
            bibliography.append(entry)
        
        return bibliography
    
    def top_core_and_recent(
        self,
        query: str,
        core_count: int = 10,
        recent_count: int = 10
    ) -> Dict[str, List[Dict]]:
        """
        Get top core (highly cited) and recent works.
        
        Args:
            query: Search query
            core_count: Number of core works to retrieve
            recent_count: Number of recent works to retrieve
        
        Returns:
            Dictionary with "core" and "recent" lists of bibliography entries
        """
        # Get core works (sorted by citation count)
        core_works = self.search_works(
            query,
            per_page=core_count,
            sort="cited_by_count:desc"
        )
        
        # Get recent works (sorted by publication date)
        recent_works = self.search_works(
            query,
            per_page=recent_count,
            sort="publication_date:desc"
        )
        
        return {
            "core": self.build_bibliography(core_works),
            "recent": self.build_bibliography(recent_works)
        }
    
    def generate_bibliography(
        self,
        core_keywords: str = "",
        core_authors: str = "",
        recent_keywords: str = ""
    ) -> Dict[str, List[Dict]]:
        """
        Generate bibliography using OpenAlex with custom parameters.
        
        Args:
            core_keywords: Keywords for core works search
            core_authors: Authors for core works filter (comma-separated)
            recent_keywords: Keywords for recent works search
        
        Returns:
            Dictionary with "core" and "recent" lists of bibliography entries
        """
        # Build core query
        core_query = core_keywords.replace(",", " ").strip() if core_keywords else ""
        
        # Build core search params
        core_params = {
            "search": core_query if core_query else "research",
            "per_page": 10,
            "sort": "cited_by_count:desc"
        }
        
        # Add author filter if provided
        if core_authors:
            author_names = [a.strip() for a in core_authors.split(",") if a.strip()]
            if author_names:
                # OpenAlex filter format for authors - use OR operator
                # Format: author.display_name:"Name1"|author.display_name:"Name2"
                author_filters = [f'author.display_name:"{name}"' for name in author_names]
                core_params["filter"] = "|".join(author_filters)
        
        # Get core works
        core_result = self._make_request("works", core_params)
        core_works = core_result.get("results", [])
        
        # Build recent query
        recent_query = recent_keywords.replace(",", " ").strip() if recent_keywords else core_query
        
        # Get recent works (sorted by publication date)
        recent_params = {
            "search": recent_query if recent_query else "research",
            "per_page": 10,
            "sort": "publication_date:desc"
        }
        
        recent_result = self._make_request("works", recent_params)
        recent_works = recent_result.get("results", [])
        
        return {
            "core": self.build_bibliography(core_works),
            "recent": self.build_bibliography(recent_works)
        }

