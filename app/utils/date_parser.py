import re
from typing import Optional

def normalize_date(date_str: str) -> Optional[str]:
    if not date_str:
        return None
    
    date_str = date_str.strip()
    
    # Matching DD.MM.YYYY
    match = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", date_str)
    if match:
        d, m, y = match.groups()
        return f"{y}-{int(m):02d}-{int(d):02d}"
    
    # Matching DD/MM/YYYY
    match = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", date_str)
    if match:
        d, m, y = match.groups()
        return f"{y}-{int(m):02d}-{int(d):02d}"
        
    # Matching ISO 8601 format directly 
    match = re.search(r"(\d{4})-(\d{2})-(\d{2})", date_str)
    if match:
        return match.group(0)

    return None
