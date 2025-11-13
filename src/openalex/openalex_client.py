"""
OpenAlex API client using pyalex library for stable and reliable searches.
"""
from pyalex import Works
import logging
from typing import List, Dict, Optional
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def search_openalex(keywords: list[str], authors: list[str] = None, limit: int = 20) -> List[Dict]:
    """
    Stable OpenAlex search using pyalex library.
    
    Args:
        keywords: List of keywords for search
        authors: List of authors for post-filter (optional)
        limit: Maximum number of results to return
    
    Returns:
        List of work dictionaries from OpenAlex
    """
    all_results = []
    
    # Normalize keywords - split by comma if string, or use list directly
    if isinstance(keywords, str):
        keywords = [kw.strip() for kw in keywords.split(",") if kw.strip()]
    
    for kw in keywords:
        if not kw or not kw.strip():
            continue
        
        logger.info(f"🔍 OpenAlex: ищу по ключевому слову: {kw}")
        
        try:
            # Use pyalex Works().search() - stable and reliable
            # Works().search() returns a query object, .get() executes the query
            query_result = Works().search(kw).get(per_page=50)
            
            if query_result:
                if isinstance(query_result, list):
                    all_results.extend(query_result)
                    logger.info(f"  ✓ Найдено {len(query_result)} результатов для '{kw}'")
                elif isinstance(query_result, dict):
                    # Single result
                    all_results.append(query_result)
                    logger.info(f"  ✓ Найден 1 результат для '{kw}'")
                else:
                    logger.warning(f"  ⚠️ Неожиданный тип результата для '{kw}': {type(query_result)}")
            else:
                logger.warning(f"  ⚠️ Нет результатов для '{kw}'")
        except Exception as e:
            logger.error(f"❌ Ошибка в OpenAlex для '{kw}': {e}")
            import traceback
            logger.error(traceback.format_exc())
            continue
    
    if not all_results:
        logger.warning("⚠️ OpenAlex не вернул результатов")
        return []
    
    # Remove duplicates by DOI or OpenAlex ID
    unique = {}
    seen_ids = set()
    
    for item in all_results:
        if not isinstance(item, dict):
            continue
        
        # Try DOI first
        doi = item.get("doi")
        if doi:
            # Normalize DOI (remove https://doi.org/ prefix)
            doi = str(doi).replace("https://doi.org/", "").replace("http://doi.org/", "")
            if doi and doi not in seen_ids:
                seen_ids.add(doi)
                unique[doi] = item
                continue
        
        # If no DOI, use OpenAlex ID
        openalex_id_full = item.get("id", "")
        if openalex_id_full:
            openalex_id = str(openalex_id_full).replace("https://openalex.org/", "")
            if openalex_id and openalex_id not in seen_ids:
                seen_ids.add(openalex_id)
                unique[openalex_id] = item
    
    results = list(unique.values())
    
    # Post-filter by authors if provided
    if authors:
        if isinstance(authors, str):
            authors = [a.strip() for a in authors.split(",") if a.strip()]
        
        filtered = []
        for work in results:
            if not isinstance(work, dict):
                continue
            
            # Check all authorships
            authorships = work.get("authorships", [])
            for auth in authorships:
                if not isinstance(auth, dict):
                    continue
                
                author = auth.get("author", {})
                if not isinstance(author, dict):
                    continue
                
                display_name = author.get("display_name", "")
                if display_name in authors:
                    filtered.append(work)
                    break
        
        results = filtered
    
    # Sort by citation count (most cited first)
    results = sorted(
        results,
        key=lambda x: x.get("cited_by_count", 0) if isinstance(x, dict) else 0,
        reverse=True
    )
    
    logger.info(f"📘 OpenAlex: найдено {len(results)} уникальных результатов")
    
    return results[:limit]


def build_bibliography(works: List[Dict]) -> List[Dict]:
    """
    Build bibliography entries from OpenAlex works.
    
    Args:
        works: List of work dictionaries from OpenAlex
    
    Returns:
        List of formatted bibliography entries
    """
    bibliography = []
    
    for work in works:
        if not isinstance(work, dict):
            continue
        
        # Extract authors
        authors = []
        authorships = work.get("authorships", [])
        if authorships:
            for authorship in authorships:
                if not isinstance(authorship, dict):
                    continue
                author = authorship.get("author", {})
                if isinstance(author, dict):
                    display_name = author.get("display_name", "Unknown")
                    if display_name:
                        authors.append(display_name)
        
        # Extract year
        publication_date = work.get("publication_date", "")
        year = publication_date.split("-")[0] if publication_date else "Unknown"
        
        # Extract DOI
        doi = work.get("doi", "")
        if doi:
            doi = str(doi).replace("https://doi.org/", "").replace("http://doi.org/", "")
        else:
            doi = ""
        
        # Extract OpenAlex ID
        openalex_id = work.get("id", "").replace("https://openalex.org/", "")
        
        # Extract source (journal/venue)
        source = "Unknown"
        primary_location = work.get("primary_location", {})
        if isinstance(primary_location, dict):
            source_obj = primary_location.get("source", {})
            if isinstance(source_obj, dict):
                source = source_obj.get("display_name", "Unknown")
        
        if source == "Unknown" and work.get("locations"):
            for loc in work["locations"]:
                if not isinstance(loc, dict):
                    continue
                source_obj = loc.get("source", {})
                if isinstance(source_obj, dict):
                    source_name = source_obj.get("display_name")
                    if source_name:
                        source = source_name
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


class OpenAlexClient:
    """
    Client for interacting with OpenAlex API using pyalex library.
    Maintains backward compatibility with existing code.
    """
    
    def __init__(self):
        """Initialize OpenAlex client."""
        # Set email for pyalex (if configured)
        if config.OPENALEX_EMAIL:
            import os
            os.environ["OPENALEX_EMAIL"] = config.OPENALEX_EMAIL
            logger.info(f"📧 OpenAlex: используется email {config.OPENALEX_EMAIL}")
    
    def search_works(
        self,
        query: str,
        per_page: int = 25,
        sort: str = "relevance_score:desc"
    ) -> List[Dict]:
        """
        Search for works in OpenAlex using pyalex.
        
        Args:
            query: Search query
            per_page: Number of results per page
            sort: Sort order (not used in pyalex, but kept for compatibility)
        
        Returns:
            List of work dictionaries
        """
        # Convert query to keywords list
        keywords = [kw.strip() for kw in query.split() if kw.strip()]
        if not keywords:
            keywords = [query]
        
        return search_openalex(keywords, limit=per_page)
    
    def build_bibliography(self, works: List[Dict]) -> List[Dict]:
        """
        Build bibliography entries from OpenAlex works.
        
        Args:
            works: List of work dictionaries from OpenAlex
        
        Returns:
            List of formatted bibliography entries
        """
        return build_bibliography(works)
    
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
        # Convert query to keywords
        keywords = [kw.strip() for kw in query.split() if kw.strip()]
        if not keywords:
            keywords = [query]
        
        # Get core works (sorted by citation count - already sorted in search_openalex)
        core_works = search_openalex(keywords, limit=core_count)
        
        # Get recent works (need to sort by date)
        recent_works_raw = search_openalex(keywords, limit=recent_count * 2)
        # Sort by publication date
        recent_works = sorted(
            recent_works_raw,
            key=lambda x: x.get("publication_date", "") if isinstance(x, dict) else "",
            reverse=True
        )[:recent_count]
        
        return {
            "core": build_bibliography(core_works),
            "recent": build_bibliography(recent_works)
        }
    
    def generate_bibliography(
        self,
        core_keywords: str = "",
        core_authors: str = "",
        recent_keywords: str = ""
    ) -> Dict[str, List[Dict]]:
        """
        Generate bibliography using pyalex for stable searches.
        Maintains backward compatibility with existing code.
        
        Args:
            core_keywords: Keywords for core works search (comma-separated string)
            core_authors: Authors for core works filter (comma-separated string)
            recent_keywords: Keywords for recent works search (comma-separated string)
        
        Returns:
            Dictionary with "core" and "recent" lists of bibliography entries
        """
        # Normalize keywords
        core_kw_list = []
        if core_keywords:
            core_kw_list = [kw.strip() for kw in core_keywords.split(",") if kw.strip()]
        
        recent_kw_list = []
        if recent_keywords:
            recent_kw_list = [kw.strip() for kw in recent_keywords.split(",") if kw.strip()]
        else:
            # Use core keywords if recent keywords not provided
            recent_kw_list = core_kw_list.copy()
        
        # Normalize authors
        authors_list = None
        if core_authors:
            authors_list = [a.strip() for a in core_authors.split(",") if a.strip()]
        
        # Search for core works
        logger.info(f"🔍 OpenAlex: поиск core работ по ключевым словам: {core_kw_list}")
        core_works = []
        if core_kw_list:
            core_works = search_openalex(core_kw_list, authors=authors_list, limit=15)
        
        # Fallback if no results
        if not core_works and core_kw_list:
            logger.warning("⚠️ Core поиск не дал результатов, пробую только первый ключ")
            core_works = search_openalex([core_kw_list[0]], authors=authors_list, limit=15)
        
        # Search for recent works
        logger.info(f"🔍 OpenAlex: поиск recent работ по ключевым словам: {recent_kw_list}")
        recent_works_raw = []
        if recent_kw_list:
            recent_works_raw = search_openalex(recent_kw_list, authors=authors_list, limit=30)
        
        # Fallback if no results
        if not recent_works_raw and recent_kw_list:
            logger.warning("⚠️ Recent поиск не дал результатов, пробую только первый ключ")
            recent_works_raw = search_openalex([recent_kw_list[0]], authors=authors_list, limit=30)
        
        # Sort recent works by publication date
        recent_works = sorted(
            recent_works_raw,
            key=lambda x: x.get("publication_date", "") if isinstance(x, dict) else "",
            reverse=True
        )[:15]
        
        return {
            "core": build_bibliography(core_works),
            "recent": build_bibliography(recent_works)
        }
