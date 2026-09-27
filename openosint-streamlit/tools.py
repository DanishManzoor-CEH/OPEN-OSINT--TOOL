import ipaddress
import json
import re
import socket
from datetime import datetime, timezone
from typing import Any, Dict
from urllib.parse import quote, urlparse

import requests

DEFAULT_TIMEOUT = 15
HIBP_API_KEY = None


def configure(timeout: int = 15, hibp_api_key: str | None = None):
    global DEFAULT_TIMEOUT, HIBP_API_KEY
    DEFAULT_TIMEOUT = max(5, min(int(timeout), 30))
    HIBP_API_KEY = hibp_api_key


def _clean_domain(value: str) -> str:
    value = value.strip()
    if "://" in value:
        value = urlparse(value).hostname or value
    value = value.split("/")[0].split(":")[0].strip(".").lower()
    return value


def _safe_request(method: str, url: str, **kwargs):
    headers = kwargs.pop("headers", {})
    headers.setdefault("User-Agent", "OpenOSINT-Streamlit/1.0 (authorized-research)")
    kwargs["headers"] = headers
    kwargs.setdefault("timeout", DEFAULT_TIMEOUT)
    response = requests.request(method, url, **kwargs)
    response.raise_for_status()
    return response


def get_domain_dns(domain: str) -> Dict[str, Any]:
    domain = _clean_domain(domain)
    records = {"domain": domain, "addresses": [], "ipv6": [], "canonical_name": None}

    try:
        infos = socket.getaddrinfo(domain, None)
        for item in infos:
            address = item[4][0]
            if ":" in address:
                if address not in records["ipv6"]:
                    records["ipv6"].append(address)
            else:
                if address not in records["addresses"]:
                    records["addresses"].append(address)
    except socket.gaierror as exc:
        records["error"] = str(exc)

    try:
        records["canonical_name"] = socket.getfqdn(domain)
    except Exception:
        pass

    return records


def get_rdap_domain(domain: str) -> Dict[str, Any]:
    domain = _clean_domain(domain)
    tld = domain.rsplit(".", 1)[-1]

    # IANA bootstrap maps a TLD to an RDAP service.
    bootstrap = _safe_request(
        "GET",
        "https://data.iana.org/rdap/dns.json",
    ).json()

    rdap_base = None
    for service in bootstrap.get("services", []):
        if tld in service[0]:
            rdap_base = service[1][0]
            break

    if not rdap_base:
        return {"domain": domain, "error": f"No RDAP service found for .{tld}"}

    url = rdap_base.rstrip("/") + "/domain/" + quote(domain, safe="")
    data = _safe_request("GET", url).json()

    events = {}
    for event in data.get("events", []):
        action = event.get("eventAction")
        date = event.get("eventDate")
        if action and date:
            events[action] = date

    nameservers = []
    for entity in data.get("nameservers", []):
        if entity.get("ldhName"):
            nameservers.append(entity["ldhName"])

    return {
        "domain": domain,
        "handle": data.get("handle"),
        "status": data.get("status", []),
        "events": events,
        "nameservers": nameservers,
        "secure_dns": data.get("secureDNS", {}),
    }


def get_ip_info(ip: str) -> Dict[str, Any]:
    ip = ip.strip()

    try:
        parsed = ipaddress.ip_address(ip)
    except ValueError:
        return {"ip": ip, "error": "Invalid IP address"}

    if parsed.is_private or parsed.is_loopback or parsed.is_reserved or parsed.is_link_local:
        return {
            "ip": ip,
            "classification": "non-public",
            "is_private": parsed.is_private,
            "is_loopback": parsed.is_loopback,
            "is_reserved": parsed.is_reserved,
            "is_link_local": parsed.is_link_local,
        }

    # ipwho.is is used because it exposes a simple public JSON endpoint.
    data = _safe_request("GET", f"https://ipwho.is/{quote(ip)}").json()
    return {
        "ip": ip,
        "success": data.get("success"),
        "type": data.get("type"),
        "continent": data.get("continent"),
        "country": data.get("country"),
        "region": data.get("region"),
        "city": data.get("city"),
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
        "isp": (data.get("connection") or {}).get("isp"),
        "organization": (data.get("connection") or {}).get("org"),
        "asn": (data.get("connection") or {}).get("asn"),
        "timezone": (data.get("timezone") or {}).get("id"),
    }


def check_public_username(username: str) -> Dict[str, Any]:
    username = username.strip().lstrip("@")
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,80}", username):
        return {"username": username, "error": "Unsupported username format"}

    sites = {
        "GitHub": f"https://github.com/{quote(username)}",
        "GitLab": f"https://gitlab.com/{quote(username)}",
        "Reddit": f"https://www.reddit.com/user/{quote(username)}/about.json",
        "Medium": f"https://medium.com/@{quote(username)}",
        "Dev.to": f"https://dev.to/{quote(username)}",
    }

    results = {}
    for site, url in sites.items():
        try:
            response = _safe_request(
                "GET",
                url,
                allow_redirects=True,
            )
            results[site] = {
                "status_code": response.status_code,
                "found": response.status_code < 400,
                "final_url": response.url,
            }
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            results[site] = {"status_code": status, "found": False}
        except requests.RequestException as exc:
            results[site] = {"error": str(exc), "found": False}

    return {"username": username, "profiles": results}


def validate_email_format(email: str) -> Dict[str, Any]:
    email = email.strip()
    pattern = r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$"
    valid = bool(re.fullmatch(pattern, email))
    domain = email.rsplit("@", 1)[1].lower() if "@" in email else None
    return {
        "email": email,
        "format_valid": valid,
        "domain": domain,
        "note": "Format validation does not prove that a mailbox exists.",
    }


def check_hibp(email: str) -> Dict[str, Any]:
    if not HIBP_API_KEY:
        return {
            "email": email,
            "enabled": False,
            "message": "HIBP lookup disabled. Configure HIBP_API_KEY in Streamlit Secrets.",
        }

    email = email.strip()
    url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{quote(email, safe='')}"
    headers = {
        "hibp-api-key": HIBP_API_KEY,
        "user-agent": "OpenOSINT-Streamlit/1.0",
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=DEFAULT_TIMEOUT,
            params={"truncateResponse": "false"},
        )

        if response.status_code == 404:
            return {
                "email": email,
                "enabled": True,
                "breached": False,
                "breaches": [],
            }

        response.raise_for_status()
        data = response.json()

        breaches = []
        for item in data:
            breaches.append({
                "name": item.get("Name"),
                "title": item.get("Title"),
                "domain": item.get("Domain"),
                "breach_date": item.get("BreachDate"),
                "data_classes": item.get("DataClasses", []),
            })

        return {
            "email": email,
            "enabled": True,
            "breached": bool(breaches),
            "breaches": breaches,
            "warning": "Breach presence does not by itself prove current account compromise.",
        }

    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else None
        return {"email": email, "enabled": True, "error": f"HIBP HTTP status {status}"}
    except requests.RequestException as exc:
        return {"email": email, "enabled": True, "error": str(exc)}


def generate_dorks(query: str) -> Dict[str, Any]:
    query = query.strip()
    if not query:
        return {"error": "Query is empty"}

    # These are search-query templates only. The app does not automatically
    # search private systems or attempt authentication bypasses.
    templates = [
        f'"{query}"',
        f'"{query}" filetype:pdf',
        f'"{query}" filetype:docx',
        f'"{query}" site:github.com',
        f'"{query}" site:gitlab.com',
        f'"{query}" site:pastebin.com',
    ]
    return {
        "query": query,
        "generated_queries": templates,
        "note": "These are passive search templates. Review and use them only against authorized/public information.",
    }


def get_http_headers(url: str) -> Dict[str, Any]:
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url

    try:
        response = _safe_request("HEAD", url, allow_redirects=True)
        return {
            "requested_url": url,
            "final_url": response.url,
            "status_code": response.status_code,
            "headers": dict(response.headers),
        }
    except requests.RequestException as exc:
        return {"requested_url": url, "error": str(exc)}


def get_public_robots(url: str) -> Dict[str, Any]:
    domain = _clean_domain(url)
    robots_url = f"https://{domain}/robots.txt"

    try:
        response = _safe_request("GET", robots_url)
        return {
            "url": robots_url,
            "status_code": response.status_code,
            "content": response.text[:12000],
        }
    except requests.RequestException as exc:
        return {"url": robots_url, "error": str(exc)}


TOOL_FUNCTIONS = {
    "get_domain_dns": get_domain_dns,
    "get_rdap_domain": get_rdap_domain,
    "get_ip_info": get_ip_info,
    "check_public_username": check_public_username,
    "validate_email_format": validate_email_format,
    "check_hibp": check_hibp,
    "generate_dorks": generate_dorks,
    "get_http_headers": get_http_headers,
    "get_public_robots": get_public_robots,
}


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_domain_dns",
            "description": "Resolve a public domain to IPv4/IPv6 addresses and basic DNS hostname information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "domain": {"type": "string", "description": "Public domain name, such as example.com"}
                },
                "required": ["domain"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_rdap_domain",
            "description": "Query public RDAP registration metadata for a domain.",
            "parameters": {
                "type": "object",
                "properties": {
                    "domain": {"type": "string"}
                },
                "required": ["domain"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_ip_info",
            "description": "Get public IP geolocation and network/ASN metadata. Do not use this to infer a person's precise location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ip": {"type": "string"}
                },
                "required": ["ip"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_public_username",
            "description": "Check whether a username has publicly reachable profile pages on a small set of common platforms. Presence is not proof of identity or ownership.",
            "parameters": {
                "type": "object",
                "properties": {
                    "username": {"type": "string"}
                },
                "required": ["username"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "validate_email_format",
            "description": "Validate email syntax and extract its domain. Does not verify mailbox ownership.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string"}
                },
                "required": ["email"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_hibp",
            "description": "Check a public email address against Have I Been Pwned using an API key configured by the app owner. Only use for authorized research.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string"}
                },
                "required": ["email"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_dorks",
            "description": "Generate passive search query templates for public web research. It does not execute the searches.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_http_headers",
            "description": "Fetch public HTTP response headers from a website and follow redirects.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"}
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_public_robots",
            "description": "Retrieve a site's public robots.txt file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"}
                },
                "required": ["url"],
            },
        },
    },
]
