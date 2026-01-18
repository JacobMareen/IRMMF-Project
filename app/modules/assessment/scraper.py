"""
Service to scrape website content and analyze it.
"""
from __future__ import annotations
import asyncio
import html
import ipaddress
import re
from typing import Dict, List, Set, Tuple, Any
import logging

import urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_MAX_PAGES = 6
_MAX_BYTES = 500_000
_USER_AGENT = "IRMMF-IntakeScraper/1.0"


class _HTMLCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: List[str] = []
        self.text_chunks: List[str] = []
        self._skip_tag_depth = 0

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip_tag_depth += 1
            return
        if tag == "a":
            for attr, value in attrs:
                if attr == "href" and value:
                    self.links.append(value)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._skip_tag_depth > 0:
            self._skip_tag_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_tag_depth:
            return
        data = data.strip()
        if data:
            self.text_chunks.append(data)


def _is_private_host(hostname: str) -> bool:
    try:
        ip = ipaddress.ip_address(hostname)
        return ip.is_private or ip.is_loopback or ip.is_link_local
    except ValueError:
        return hostname in {"localhost", "127.0.0.1", "::1"} or hostname.endswith(".local")


def _is_safe_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    if not parsed.hostname:
        return False
    return not _is_private_host(parsed.hostname)


def _same_host(url: str, base_url: str) -> bool:
    return urlparse(url).hostname == urlparse(base_url).hostname


async def _fetch_with_tool(url: str) -> str:
    """
    Fetches content from a URL with urllib.
    """
    try:
        if not _is_safe_url(url):
            logger.warning("Blocked unsafe URL: %s", url)
            return ""
        req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        with urllib.request.urlopen(req, timeout=6) as response:
            raw = response.read(_MAX_BYTES + 1)
            if len(raw) > _MAX_BYTES:
                logger.warning("Truncated response from %s", url)
                raw = raw[:_MAX_BYTES]
            return raw.decode("utf-8", errors="ignore")
    except Exception as e:
        logger.error(f"Error fetching URL {url}: {e}")
        return ""


def _find_links(base_url: str, html_content: str, keywords: List[str]) -> Set[str]:
    """
    Finds links on a page that contain certain keywords.
    """
    found_links: Set[str] = set()
    parser = _HTMLCollector()
    parser.feed(html_content)
    for link in parser.links:
        link_lower = link.lower()
        for keyword in keywords:
            if keyword in link_lower:
                full_url = urljoin(base_url, link)
                if _is_safe_url(full_url) and _same_host(full_url, base_url):
                    found_links.add(full_url)
                break
    return found_links


def _extract_text_and_links(html_content: str) -> Tuple[str, List[str]]:
    parser = _HTMLCollector()
    parser.feed(html_content)
    text = " ".join(parser.text_chunks)
    return html.unescape(text), parser.links


async def _get_text_from_url(url: str) -> str:
    """Gets the raw text content from a given URL."""
    logger.info(f"Fetching text from {url}...")
    html_content = await _fetch_with_tool(url)
    if html_content:
        text, _ = _extract_text_and_links(html_content)
        return " ".join(text.split())
    return ""


def _find_keyword_hits(text: str, keywords: Dict[str, List[str]]) -> List[str]:
    hits = []
    text_lower = text.lower()
    for label, values in keywords.items():
        for value in values:
            if value.lower() in text_lower:
                hits.append(label)
                break
    return hits


def _analyze_text_with_heuristics(text: str) -> Dict[str, str | List[str]]:
    """
    Heuristic analysis to infer intake hints from public website text.
    Aligned with v10 streamlined intake structure.
    """
    logger.info("Running heuristic analysis on scraped text...")

    # INT-ORG-01: Primary industry sector
    industry_keywords = {
        "Financial Services": ["bank", "fintech", "financial services", "investment", "wealth", "trading"],
        "Healthcare": ["hospital", "healthcare", "pharma", "clinical", "patient", "medical"],
        "Technology / Software": ["software", "saas", "cloud", "ai", "machine learning", "tech company"],
        "Manufacturing": ["manufacturing", "factory", "industrial", "production", "assembly"],
        "Retail / E-commerce": ["retail", "ecommerce", "store", "consumer", "shopping"],
        "Energy / Utilities": ["energy", "utility", "oil", "gas", "renewable", "power"],
        "Government / Public Sector": ["government", "public sector", "municipal", "agency", "federal"],
        "Education": ["education", "university", "school", "academic", "learning"],
        "Professional Services": ["consulting", "advisory", "professional services", "audit"],
        "Media / Entertainment": ["media", "entertainment", "publishing", "broadcasting"],
        "Telecommunications": ["telecom", "telecommunications", "network", "carrier"],
        "Transportation / Logistics": ["transportation", "logistics", "shipping", "freight"],
        "Insurance": ["insurance", "underwriting", "claims", "actuarial"],
        "Other": [],
    }

    # INT-REG-01: Regulatory frameworks (multi-select)
    regulation_keywords = {
        "GDPR": ["gdpr", "general data protection"],
        "SOX": ["sox", "sarbanes-oxley", "sarbanes oxley"],
        "HIPAA": ["hipaa", "health insurance portability"],
        "PCI-DSS": ["pci", "payment card", "pci-dss"],
        "CCPA": ["ccpa", "cpra", "california consumer privacy"],
        "NIS2": ["nis2", "nis 2", "network information security"],
        "DORA": ["dora", "digital operational resilience"],
        "GLBA": ["glba", "gramm-leach-bliley"],
        "FERPA": ["ferpa", "educational privacy"],
        "FedRAMP": ["fedramp", "federal risk"],
        "CMMC": ["cmmc", "cybersecurity maturity"],
        "ITAR": ["itar", "international traffic arms"],
        "Export Controls": ["export control", "ear"],
        "Whistleblowing Directive": ["whistleblow", "directive 2019/1937"],
        "FISMA": ["fisma", "federal information security"],
        "DFARS": ["dfars", "defense federal"],
        "ISO 27001": ["iso 27001", "iso27001"],
        "None": [],
    }

    # INT-ORG-03: Geographic footprint
    footprint_keywords = {
        "Global (all continents)": ["global", "worldwide", "multinational", "international", "all continents"],
        "Global (multi-region)": ["multiple regions", "emea", "apac", "americas"],
        "Regional (multiple countries)": ["regional", "europe", "asia pacific", "north america"],
        "Single country": ["domestic", "national", "country"],
    }

    # INT-ORG-02: Employee count hints
    size_keywords = {
        "100,000+": ["fortune 500", "global enterprise", "100000", "hundred thousand"],
        "20,000-100,000": ["large enterprise", "20000"],
        "5,000-20,000": ["enterprise", "5000"],
        "1,000-5,000": ["mid-size", "1000"],
        "251-1,000": ["250", "500"],
        "51-250": ["small", "startup", "50"],
        "1-50": ["very small", "micro"],
    }

    # INT-TECH-01: IT environment
    it_env_keywords = {
        "Cloud-native (100% cloud)": ["cloud-native", "fully cloud", "100% cloud"],
        "Multi-cloud (AWS + Azure/GCP)": ["multi-cloud", "aws azure", "aws gcp"],
        "Hybrid (on-prem + cloud)": ["hybrid", "on-premises cloud", "hybrid cloud"],
        "Primarily cloud (>70%)": ["primarily cloud", "mostly cloud", "cloud-first"],
        "On-premises (>70% data centers)": ["on-premises", "data center", "on-prem"],
    }

    # INT-TECH-03: Technology platforms (multi-select)
    platform_keywords = {
        "Microsoft 365": ["microsoft 365", "m365", "office 365", "o365"],
        "Google Workspace": ["google workspace", "g suite", "gsuite"],
        "AWS": ["aws", "amazon web services"],
        "Azure": ["azure", "microsoft azure"],
        "GCP": ["gcp", "google cloud platform"],
        "Salesforce": ["salesforce", "sfdc"],
        "SAP": ["sap"],
        "Oracle": ["oracle"],
        "ServiceNow": ["servicenow"],
        "Slack": ["slack"],
        "Zoom": ["zoom"],
        "Other": [],
    }

    industries = _find_keyword_hits(text, industry_keywords)
    regulations = _find_keyword_hits(text, regulation_keywords)
    footprints = _find_keyword_hits(text, footprint_keywords)
    sizes = _find_keyword_hits(text, size_keywords)
    it_envs = _find_keyword_hits(text, it_env_keywords)
    platforms = _find_keyword_hits(text, platform_keywords)

    return {
        "industries": industries,
        "regulations": regulations,
        "footprints": footprints,
        "company_sizes": sizes,
        "it_environments": it_envs,
        "platforms": platforms,
    }


def _normalize(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def _match_option(preferred: List[str], options: List[str]) -> str:
    if not options:
        return "Unknown"
    options_norm = [(opt, _normalize(opt)) for opt in options]
    for pref in preferred:
        pref_norm = _normalize(pref)
        if not pref_norm:
            continue
        for opt, opt_norm in options_norm:
            if pref_norm == opt_norm:
                return opt
        for opt, opt_norm in options_norm:
            if pref_norm in opt_norm or opt_norm in pref_norm:
                return opt
    return options[0]


def _match_multi(preferred: List[str], options: List[str], max_items: int = 3) -> str:
    if not options:
        return "Unknown"
    matches: List[str] = []
    options_norm = [(opt, _normalize(opt)) for opt in options]
    for pref in preferred:
        pref_norm = _normalize(pref)
        if not pref_norm:
            continue
        for opt, opt_norm in options_norm:
            if opt in matches:
                continue
            if pref_norm == opt_norm or pref_norm in opt_norm or opt_norm in pref_norm:
                matches.append(opt)
                break
        if len(matches) >= max_items:
            break
    return ", ".join(matches) if matches else options[0]


def suggest_intake_answers(
    analysis: Dict[str, str | List[str]],
    intake_options: Dict[str, Any],
) -> Dict[str, str]:
    """
    Map analysis results to v10 streamlined intake questions.
    Aligned with 25-question intake structure (no assessment purpose questions).
    """
    industries = analysis.get("industries") or []
    footprints = analysis.get("footprints") or []
    sizes = analysis.get("company_sizes") or []
    regulations = analysis.get("regulations") or []
    it_envs = analysis.get("it_environments") or []
    platforms = analysis.get("platforms") or []

    # Map to v10 intake ListRef names
    industry_opts = intake_options.get("IndustryCode") or []
    employee_opts = intake_options.get("EmployeeCount") or []
    footprint_opts = intake_options.get("GeographicFootprint") or []
    revenue_opts = intake_options.get("AnnualRevenue") or []
    regulatory_opts = intake_options.get("RegulatoryFramework") or []
    it_env_opts = intake_options.get("ITEnvironment") or []
    platform_opts = intake_options.get("TechnologyPlatforms") or []

    # INT-ORG-01: Primary industry sector
    industry = _match_option(industries, industry_opts)

    # INT-ORG-02: Employee count
    employee_count = _match_option(sizes, employee_opts)

    # INT-ORG-03: Geographic footprint
    geographic_footprint = _match_option(footprints, footprint_opts)

    # INT-ORG-05: Annual revenue (infer from employee count)
    revenue_band = _match_option([employee_count], revenue_opts)
    if revenue_opts and revenue_band == revenue_opts[0]:
        size_lower = employee_count.lower()
        if "100,000" in size_lower or "100000" in size_lower:
            revenue_band = _match_option(["$50B+"], revenue_opts)
        elif "20,000" in size_lower or "20000" in size_lower:
            revenue_band = _match_option(["$10B-$50B"], revenue_opts)
        elif "5,000" in size_lower or "5000" in size_lower:
            revenue_band = _match_option(["$1B-$10B"], revenue_opts)
        elif "1,000" in size_lower or "1000" in size_lower:
            revenue_band = _match_option(["$250M-$1B"], revenue_opts)
        elif "251" in size_lower or "250" in size_lower:
            revenue_band = _match_option(["$50M-$250M"], revenue_opts)
        elif "51" in size_lower or "50" in size_lower:
            revenue_band = _match_option(["$10M-$50M"], revenue_opts)
        else:
            revenue_band = _match_option(["<$10M"], revenue_opts)

    # INT-REG-01: Regulatory frameworks (multi-select)
    regulatory_frameworks = _match_multi(regulations, regulatory_opts, max_items=5)

    # INT-TECH-01: IT environment
    it_environment = _match_option(it_envs, it_env_opts)

    # INT-TECH-03: Technology platforms (multi-select)
    technology_platforms = _match_multi(platforms, platform_opts, max_items=6)

    return {
        "INT-ORG-01": industry,
        "INT-ORG-02": employee_count,
        "INT-ORG-03": geographic_footprint,
        "INT-ORG-05": revenue_band,
        "INT-REG-01": regulatory_frameworks,
        "INT-TECH-01": it_environment,
        "INT-TECH-03": technology_platforms,
    }


async def scrape_and_analyze_website(base_url: str) -> Dict[str, str | List[str]]:
    """
    Main service function to scrape a website, find key pages,
    and run a heuristic analysis on their content.
    """
    logger.info(f"Starting scrape for base URL: {base_url}")
    if not _is_safe_url(base_url):
        return {"error": "Unsafe URL blocked."}

    main_page_html = await _fetch_with_tool(base_url)
    if not main_page_html:
        logger.error("Could not fetch main page. Aborting.")
        return {"error": "Could not fetch the provided URL."}

    key_pages = _find_links(base_url, main_page_html, ['privacy', 'about', 'terms', 'legal'])
    key_pages.add(base_url)
    if len(key_pages) > _MAX_PAGES:
        key_pages = set(list(key_pages)[:_MAX_PAGES])

    logger.info(f"Found {len(key_pages)} key pages to analyze: {key_pages}")

    tasks = [_get_text_from_url(url) for url in key_pages]
    contents = await asyncio.gather(*tasks)
    combined_text = " ".join(contents)

    if not combined_text.strip():
        logger.error("Could not extract any text content from the website.")
        return {"error": "Could not extract text content from the website."}

    max_text_len = 15000
    analysis_result = _analyze_text_with_heuristics(combined_text[:max_text_len])

    logger.info(f"Analysis complete. Results: {analysis_result}")
    return analysis_result
