import ipaddress
import re
import socket
from urllib.parse import quote, urlparse
import requests

TIMEOUT = 15
HIBP_API_KEY = None

def configure(timeout=15, hibp_api_key=None):
    global TIMEOUT, HIBP_API_KEY
    TIMEOUT = max(5, min(int(timeout), 30))
    HIBP_API_KEY = hibp_api_key

def request(method, url, **kwargs):
    headers = kwargs.pop("headers", {})
    headers.setdefault("User-Agent", "OpenOSINT-AI-V2/1.0")
    kwargs["headers"] = headers
    kwargs.setdefault("timeout", TIMEOUT)
    r = requests.request(method, url, **kwargs)
    r.raise_for_status()
    return r

def domain(value):
    value = value.strip()
    if "://" in value:
        value = urlparse(value).hostname or value
    return value.split("/")[0].split(":")[0].strip(".").lower()

def get_domain_dns(domain_name):
    d = domain(domain_name)
    out = {"domain": d, "ipv4": [], "ipv6": []}
    try:
        for item in socket.getaddrinfo(d, None):
            a = item[4][0]
            key = "ipv6" if ":" in a else "ipv4"
            if a not in out[key]:
                out[key].append(a)
        out["canonical_name"] = socket.getfqdn(d)
    except socket.gaierror as e:
        out["error"] = str(e)
    return out

def get_rdap_domain(domain_name):
    d = domain(domain_name)
    tld = d.rsplit(".", 1)[-1]
    bootstrap = request("GET", "https://data.iana.org/rdap/dns.json").json()
    base = None
    for service in bootstrap.get("services", []):
        if tld in service[0]:
            base = service[1][0]
            break
    if not base:
        return {"domain": d, "error": f"No RDAP service for .{tld}"}
    data = request("GET", base.rstrip("/") + "/domain/" + quote(d)).json()
    events = {x.get("eventAction"): x.get("eventDate") for x in data.get("events", []) if x.get("eventAction")}
    return {
        "domain": d,
        "handle": data.get("handle"),
        "status": data.get("status", []),
        "events": events,
        "nameservers": [x.get("ldhName") for x in data.get("nameservers", []) if x.get("ldhName")],
        "secure_dns": data.get("secureDNS", {}),
    }

def get_ip_info(ip):
    try:
        parsed = ipaddress.ip_address(ip.strip())
    except ValueError:
        return {"ip": ip, "error": "Invalid IP address"}
    if any([parsed.is_private, parsed.is_loopback, parsed.is_reserved, parsed.is_link_local]):
        return {"ip": ip, "classification": "non-public", "is_private": parsed.is_private, "is_loopback": parsed.is_loopback}
    data = request("GET", f"https://ipwho.is/{quote(ip.strip())}").json()
    c = data.get("connection") or {}
    tz = data.get("timezone") or {}
    return {
        "ip": ip, "success": data.get("success"), "type": data.get("type"),
        "continent": data.get("continent"), "country": data.get("country"),
        "region": data.get("region"), "city": data.get("city"),
        "latitude": data.get("latitude"), "longitude": data.get("longitude"),
        "isp": c.get("isp"), "organization": c.get("org"), "asn": c.get("asn"),
        "timezone": tz.get("id"),
    }

def validate_email_format(email):
    email = email.strip()
    valid = bool(re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+", email))
    return {"email": email, "format_valid": valid, "domain": email.rsplit("@", 1)[1].lower() if "@" in email else None, "note": "Syntax validation does not prove mailbox ownership."}

def check_hibp(email):
    if not HIBP_API_KEY:
        return {"enabled": False, "email": email, "message": "HIBP_API_KEY is not configured."}
    url = "https://haveibeenpwned.com/api/v3/breachedaccount/" + quote(email, safe="")
    headers = {"hibp-api-key": HIBP_API_KEY, "user-agent": "OpenOSINT-AI-V2/1.0"}
    try:
        r = requests.get(url, headers=headers, params={"truncateResponse": "false"}, timeout=TIMEOUT)
        if r.status_code == 404:
            return {"enabled": True, "email": email, "breached": False, "breaches": []}
        r.raise_for_status()
        breaches = [{"name": x.get("Name"), "title": x.get("Title"), "domain": x.get("Domain"), "breach_date": x.get("BreachDate"), "data_classes": x.get("DataClasses", [])} for x in r.json()]
        return {"enabled": True, "email": email, "breached": bool(breaches), "breaches": breaches}
    except requests.RequestException as e:
        return {"enabled": True, "email": email, "error": str(e)}

def check_public_username(username):
    u = username.strip().lstrip("@")
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,80}", u):
        return {"username": u, "error": "Unsupported username format"}
    sites = {
        "GitHub": f"https://github.com/{quote(u)}",
        "GitLab": f"https://gitlab.com/{quote(u)}",
        "Reddit": f"https://www.reddit.com/user/{quote(u)}/about.json",
        "Medium": f"https://medium.com/@{quote(u)}",
        "Dev.to": f"https://dev.to/{quote(u)}",
    }
    results = {}
    for site, url in sites.items():
        try:
            r = request("GET", url, allow_redirects=True)
            results[site] = {"found": r.status_code < 400, "status_code": r.status_code, "final_url": r.url}
        except requests.HTTPError as e:
            results[site] = {"found": False, "status_code": e.response.status_code if e.response else None}
        except requests.RequestException as e:
            results[site] = {"found": False, "error": str(e)}
    return {"username": u, "profiles": results, "warning": "A matching username does not establish identity or ownership."}

def get_http_headers(url):
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url
    try:
        r = request("HEAD", url, allow_redirects=True)
        return {"requested_url": url, "final_url": r.url, "status_code": r.status_code, "headers": dict(r.headers)}
    except requests.RequestException as e:
        return {"requested_url": url, "error": str(e)}

def get_public_robots(url):
    d = domain(url)
    target = f"https://{d}/robots.txt"
    try:
        r = request("GET", target)
        return {"url": target, "status_code": r.status_code, "content": r.text[:12000]}
    except requests.RequestException as e:
        return {"url": target, "error": str(e)}

def generate_dorks(query):
    q = query.strip()
    return {"query": q, "generated_queries": [f'"{q}"', f'"{q}" filetype:pdf', f'"{q}" site:github.com', f'"{q}" site:gitlab.com', f'"{q}" site:pastebin.com'], "note": "Queries are generated only; they are not executed."}

TOOL_FUNCTIONS = {
    "get_domain_dns": get_domain_dns, "get_rdap_domain": get_rdap_domain,
    "get_ip_info": get_ip_info, "validate_email_format": validate_email_format,
    "check_hibp": check_hibp, "check_public_username": check_public_username,
    "get_http_headers": get_http_headers, "get_public_robots": get_public_robots,
    "generate_dorks": generate_dorks,
}

def schema(name, description, field):
    return {"type": "function", "function": {"name": name, "description": description, "parameters": {"type": "object", "properties": {field: {"type": "string"}}, "required": [field]}}}

TOOL_SCHEMAS = [
    schema("get_domain_dns", "Resolve a public domain to IPv4/IPv6 addresses.", "domain"),
    schema("get_rdap_domain", "Get public RDAP registration metadata for a domain.", "domain"),
    schema("get_ip_info", "Get public IP network and approximate geolocation metadata.", "ip"),
    schema("validate_email_format", "Validate email syntax and extract its domain.", "email"),
    schema("check_hibp", "Check an email against HIBP if the app owner configured HIBP_API_KEY.", "email"),
    schema("check_public_username", "Check public profile availability on selected sites; presence does not prove identity.", "username"),
    schema("get_http_headers", "Fetch public HTTP response headers from a website.", "url"),
    schema("get_public_robots", "Retrieve a public robots.txt file.", "url"),
    schema("generate_dorks", "Generate passive search-query templates without executing them.", "query"),
]
