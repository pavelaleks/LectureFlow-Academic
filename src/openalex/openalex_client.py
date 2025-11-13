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

