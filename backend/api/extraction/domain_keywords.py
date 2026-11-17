"""Domain keyword extraction for Jaccard matching signal.

Domain keywords are distinct from technical skills. They represent
domains, fields, or areas of expertise (e.g., NLP, VLSI, Fintech)
rather than specific technologies or tools.

This module extracts domain keywords using a fixed vocabulary separate
from the skills dictionary to avoid conflating the two concepts.
"""

import re
from dataclasses import dataclass
from typing import Final

# Fixed domain keyword vocabulary
# These are separate from technical skills and represent domains/fields
_DOMAIN_KEYWORDS: Final[dict[str, list[str]]] = {
    "Artificial Intelligence": ["ai", "artificial intelligence"],
    "Machine Learning": ["ml", "machine learning"],
    "Deep Learning": ["deep learning"],
    "NLP": ["nlp", "natural language processing"],
    "Computer Vision": ["computer vision", "cv"],
    "Data Science": ["data science"],
    "Data Engineering": ["data engineering"],
    "Data Analytics": ["data analytics"],
    "Big Data": ["big data"],
    "Fintech": ["fintech", "financial technology"],
    "Healthtech": ["healthtech", "healthcare technology"],
    "Edtech": ["edtech", "education technology"],
    "Legaltech": ["legaltech", "legal technology"],
    "Regtech": ["regtech", "regulatory technology"],
    "Insurtech": ["insurtech", "insurance technology"],
    "Proptech": ["proptech", "property technology"],
    "Agritech": ["agritech", "agricultural technology"],
    "CleanTech": ["cleantech", "clean technology"],
    "Greentech": ["greentech", "green technology"],
    "E-commerce": ["ecommerce", "e-commerce", "electronic commerce"],
    "SaaS": ["saas", "software as a service"],
    "PaaS": ["paas", "platform as a service"],
    "IaaS": ["iaas", "infrastructure as a service"],
    "B2B": ["b2b", "business to business"],
    "B2C": ["b2c", "business to consumer"],
    "C2C": ["c2c", "consumer to consumer"],
    "API Economy": ["api economy"],
    "Blockchain": ["blockchain"],
    "Cryptocurrency": ["cryptocurrency", "crypto"],
    "Web3": ["web3", "web 3"],
    "DeFi": ["defi", "decentralized finance"],
    "NFT": ["nft", "non-fungible token"],
    "Metaverse": ["metaverse"],
    "Gaming": ["gaming"],
    "Esports": ["esports", "e-sports"],
    "Social Media": ["social media"],
    "Streaming": ["streaming"],
    "Content Delivery": ["content delivery", "cdn"],
    "Cybersecurity": ["cybersecurity", "cyber security"],
    "InfoSec": ["infosec", "information security"],
    "DevSecOps": ["devsecops"],
    "Cloud Computing": ["cloud computing"],
    "Edge Computing": ["edge computing"],
    "Distributed Systems": ["distributed systems"],
    "Microservices": ["microservices"],
    "SOA": ["soa", "service oriented architecture"],
    "Event-Driven": ["event-driven", "event driven"],
    "Real-time": ["real-time", "realtime"],
    "High-Performance": ["high-performance", "high performance"],
    "Scalability": ["scalability", "scalable"],
    "Reliability": ["reliability", "reliable"],
    "Availability": ["availability", "available"],
    "Fault Tolerance": ["fault tolerance", "fault-tolerant"],
    "Disaster Recovery": ["disaster recovery"],
    "Business Continuity": ["business continuity"],
    "Compliance": ["compliance"],
    "Governance": ["governance"],
    "Risk Management": ["risk management"],
    "Audit": ["audit", "auditing"],
    "Forensics": ["forensics", "digital forensics"],
    "Privacy": ["privacy"],
    "Data Protection": ["data protection"],
    "GDPR": ["gdpr"],
    "HIPAA": ["hipaa"],
    "SOC 2": ["soc 2"],
    "ISO 27001": ["iso 27001"],
    "PCI DSS": ["pci dss"],
    "Agile": ["agile"],
    "Scrum": ["scrum"],
    "Kanban": ["kanban"],
    "Lean": ["lean"],
    "Waterfall": ["waterfall"],
    "DevOps": ["devops"],
    "CI/CD": ["ci/cd", "cicd", "continuous integration", "continuous delivery"],
    "Test Automation": ["test automation"],
    "Quality Assurance": ["quality assurance", "qa"],
    "User Experience": ["user experience", "ux"],
    "User Interface": ["user interface", "ui"],
    "Product Management": ["product management"],
    "Project Management": ["project management"],
    "Agile Coaching": ["agile coaching"],
    "Scrum Master": ["scrum master"],
    "Product Owner": ["product owner"],
    "Business Analysis": ["business analysis", "ba"],
    "Systems Analysis": ["systems analysis", "sa"],
    "Enterprise Architecture": ["enterprise architecture"],
    "Solution Architecture": ["solution architecture"],
    "Technical Architecture": ["technical architecture"],
    "Software Architecture": ["software architecture"],
    "VLSI": ["vlsi", "very large scale integration"],
    "Embedded Systems": ["embedded systems"],
    "IoT": ["iot", "internet of things"],
    "Robotics": ["robotics"],
    "Automation": ["automation"],
    "Industrial Automation": ["industrial automation"],
    "Process Control": ["process control"],
    "Manufacturing": ["manufacturing"],
    "Supply Chain": ["supply chain"],
    "Logistics": ["logistics"],
    "Transportation": ["transportation"],
    "Automotive": ["automotive"],
    "Aerospace": ["aerospace"],
    "Defense": ["defense"],
    "Telecommunications": ["telecommunications", "telecom"],
    "Networking": ["networking"],
    "5G": ["5g"],
    "4G": ["4g"],
    "SDN": ["sdn", "software defined networking"],
    "NFV": ["nfv", "network function virtualization"],
    "Telemedicine": ["telemedicine"],
    "Telehealth": ["telehealth"],
    "Digital Health": ["digital health"],
    "Wearables": ["wearables"],
    "Fitness Tech": ["fitness tech"],
    "Wellness Tech": ["wellness tech"],
    "Mental Health": ["mental health"],
    "Biotech": ["biotech", "biotechnology"],
    "Pharma": ["pharma", "pharmaceutical"],
    "Life Sciences": ["life sciences"],
    "Genomics": ["genomics"],
    "Proteomics": ["proteomics"],
    "Bioinformatics": ["bioinformatics"],
    "Computational Biology": ["computational biology"],
    "Chemoinformatics": ["chemoinformatics"],
    "Materials Science": ["materials science"],
    "Nanotechnology": ["nanotechnology", "nanotech"],
    "Quantum Computing": ["quantum computing"],
    "High Energy Physics": ["high energy physics"],
    "Particle Physics": ["particle physics"],
    "Astrophysics": ["astrophysics"],
    "Climate Tech": ["climate tech"],
    "Sustainability": ["sustainability"],
    "Renewable Energy": ["renewable energy"],
    "Clean Energy": ["clean energy"],
    "Solar Energy": ["solar energy"],
    "Wind Energy": ["wind energy"],
    "Energy Storage": ["energy storage"],
    "Battery Tech": ["battery tech"],
    "Smart Grid": ["smart grid"],
    "Urban Tech": ["urban tech"],
    "Smart Cities": ["smart cities"],
    "Mobility": ["mobility"],
    "Transportation as a Service": ["transportation as a service", "taas"],
    "Last Mile Delivery": ["last mile delivery"],
    "On-Demand Economy": ["on-demand economy"],
    "Gig Economy": ["gig economy"],
    "Remote Work": ["remote work"],
    "Hybrid Work": ["hybrid work"],
    "Future of Work": ["future of work"],
    "Digital Transformation": ["digital transformation"],
    "Digital Innovation": ["digital innovation"],
    "Open Source": ["open source"],
    "Open Innovation": ["open innovation"],
    "Collaboration": ["collaboration"],
    "Knowledge Management": ["knowledge management"],
    "Organizational Design": ["organizational design"],
    "Change Management": ["change management"],
    "Culture": ["culture"],
    "Diversity and Inclusion": ["diversity and inclusion", "d&i"],
    "DEI": ["dei", "diversity equity inclusion"],
    "Employee Experience": ["employee experience"],
    "HR Tech": ["hr tech", "hr technology"],
    "Recruitment Tech": ["recruitment tech"],
    "Talent Management": ["talent management"],
    "Learning and Development": ["learning and development", "l&d"],
    "Performance Management": ["performance management"],
    "Compensation and Benefits": ["compensation and benefits"],
    "Payroll": ["payroll"],
    "Benefits Administration": ["benefits administration"],
    "People Analytics": ["people analytics"],
    "Workforce Planning": ["workforce planning"],
    "Succession Planning": ["succession planning"],
    "Talent Acquisition": ["talent acquisition"],
    "Employer Branding": ["employer branding"],
    "Employee Engagement": ["employee engagement"],
    "Retention": ["retention"],
    "Turnover": ["turnover"],
    "Churn": ["churn"],
    "Customer Success": ["customer success"],
    "Customer Experience": ["customer experience", "cx"],
    "Customer Service": ["customer service"],
    "Support": ["support"],
    "Help Desk": ["help desk"],
    "Technical Support": ["technical support"],
    "Field Service": ["field service"],
    "Service Management": ["service management"],
    "ITSM": ["itsm", "it service management"],
    "ITIL": ["itil"],
    "ServiceNow": ["servicenow"],
    "CRM": ["crm", "customer relationship management"],
    "Salesforce": ["salesforce"],
    "Marketing Automation": ["marketing automation"],
    "MarTech": ["martech", "marketing technology"],
    "AdTech": ["adtech", "advertising technology"],
    "Programmatic Advertising": ["programmatic advertising"],
    "Demand Generation": ["demand generation"],
    "Lead Generation": ["lead generation"],
    "Account-Based Marketing": ["account-based marketing", "abm"],
    "Inbound Marketing": ["inbound marketing"],
    "Content Marketing": ["content marketing"],
    "Social Media Marketing": ["social media marketing"],
    "Email Marketing": ["email marketing"],
    "SEO": ["seo", "search engine optimization"],
    "SEM": ["sem", "search engine marketing"],
    "PPC": ["ppc", "pay per click"],
    "Conversion Rate Optimization": ["conversion rate optimization", "cro"],
    "A/B Testing": ["a/b testing", "ab testing"],
    "Web Analytics": ["web analytics"],
    "Marketing Analytics": ["marketing analytics"],
    "Attribution": ["attribution"],
    "Customer Lifetime Value": ["customer lifetime value", "clv", "ltv"],
    "CAC": ["cac", "customer acquisition cost"],
    "ROI": ["roi", "return on investment"],
    "ROAS": ["roas", "return on ad spend"],
    "Revenue Operations": ["revenue operations", "revops"],
    "Sales Operations": ["sales operations", "salesops"],
    "Sales Enablement": ["sales enablement"],
    "Pipeline Management": ["pipeline management"],
    "Forecasting": ["forecasting"],
    "Quota Management": ["quota management"],
    "Compensation Planning": ["compensation planning"],
    "Sales Performance Management": ["sales performance management"],
    "Partner Management": ["partner management"],
    "Channel Sales": ["channel sales"],
    "Indirect Sales": ["indirect sales"],
    "Direct Sales": ["direct sales"],
    "Field Sales": ["field sales"],
    "Inside Sales": ["inside sales"],
    "SDR": ["sdr", "sales development representative"],
    "BDR": ["bdr", "business development representative"],
    "Account Executive": ["account executive", "ae"],
    "Account Manager": ["account manager", "am"],
    "Customer Success Manager": ["customer success manager", "csm"],
}


@dataclass
class DomainKeywordMatch:
    """Represents a domain keyword extracted from text."""

    keyword: str
    matched_alias: str | None = None


def extract_domain_keywords(text: str) -> list[DomainKeywordMatch]:
    """Extract domain keywords from text.

    Domain keywords are distinct from technical skills and represent
    domains, fields, or areas of expertise. This function uses a
    fixed vocabulary separate from the skills dictionary.

    Matching is case-insensitive and uses word boundaries to avoid
    false positives. Aliases are resolved to canonical keyword names.

    Args:
        text: The text to extract domain keywords from

    Returns:
        List of DomainKeywordMatch objects with canonical keywords,
        sorted deterministically by keyword name
    """
    if not text:
        return []

    text_lower = text.lower()
    found_keywords: dict[str, DomainKeywordMatch] = {}

    for canonical, aliases in _DOMAIN_KEYWORDS.items():
        # Check canonical name
        canonical_lower = canonical.lower()
        if _match_keyword(text_lower, canonical_lower):
            found_keywords[canonical] = DomainKeywordMatch(
                keyword=canonical, matched_alias=canonical
            )
            continue

        # Check aliases
        for alias in aliases:
            alias_lower = alias.lower()
            if _match_keyword(text_lower, alias_lower):
                found_keywords[canonical] = DomainKeywordMatch(
                    keyword=canonical, matched_alias=alias
                )
                break  # Found this keyword via alias, stop checking other aliases

    # Return sorted list for determinism
    return sorted(found_keywords.values(), key=lambda x: x.keyword)


def _match_keyword(text: str, keyword: str) -> bool:
    """Check if a keyword matches in text with word-boundary awareness.

    Args:
        text: The lowercase text to search in
        keyword: The lowercase keyword to match

    Returns:
        True if the keyword is found with proper boundaries
    """
    # For multi-word keywords (with spaces, slashes, hyphens), match as phrase
    if " " in keyword or "/" in keyword or "-" in keyword:
        # Handle phrases with spaces, slashes, or hyphens
        # Escape special regex characters except spaces, slashes, hyphens
        escaped = re.escape(keyword)
        escaped = escaped.replace(r"\ ", " ")
        escaped = escaped.replace(r"/", "/")
        escaped = escaped.replace(r"\-", "-")
        pattern = r"\b" + escaped + r"\b"
    else:
        # For single-word keywords, use word boundary
        pattern = r"\b" + re.escape(keyword) + r"\b"

    return bool(re.search(pattern, text))


def get_all_domain_keywords() -> list[str]:
    """Get all canonical domain keywords.

    Returns:
        List of canonical domain keyword names
    """
    return list(_DOMAIN_KEYWORDS.keys())


def get_domain_keyword_aliases(keyword: str) -> list[str] | None:
    """Get aliases for a domain keyword.

    Args:
        keyword: The canonical domain keyword name

    Returns:
        List of aliases or None if keyword not found
    """
    return _DOMAIN_KEYWORDS.get(keyword)
