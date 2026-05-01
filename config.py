"""
Configuration loader — 12-factor style.

Precedence (lowest → highest):
  1. Built-in defaults
  2. config.yaml  (or file pointed to by --config / CASAVI_CONFIG)
  3. credentials.py  (legacy fallback — prints deprecation warning)
  4. Environment variables  (CASAVI_USERNAME, CASAVI_PASSWORD, CASAVI_DOWNLOAD_DIR, CASAVI_TENANTS)
  5. CLI arguments  (--username, --password, --download-dir, --tenant, --video)
"""

import argparse
import json
import os
import sys
from urllib.parse import urlparse

import yaml

DEFAULTS = {
    'download_dir': './DownloadedFiles',
    'video': False,
    'tenants': [],
}


def _parse_args(argv=None):
    p = argparse.ArgumentParser(description='Casavi PDF Downloader')
    p.add_argument('--config', metavar='FILE',
                   help='Path to config.yaml (default: config.yaml)')
    p.add_argument('--username', metavar='EMAIL')
    p.add_argument('--password', metavar='PASS')
    p.add_argument('--download-dir', dest='download_dir', metavar='DIR')
    p.add_argument('--tenant', dest='filter_tenants', action='append', metavar='NAME',
                   help='Only process this tenant name (repeatable)')
    p.add_argument('--video', action='store_true',
                   help='Record debug videos to ./debug-videos/')
    return p.parse_args(argv)


def _load_yaml(path, required=False):
    if not os.path.exists(path):
        if required:
            print(f"ERROR: Config file not found: {path}", file=sys.stderr)
            sys.exit(1)
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def _load_legacy_credentials():
    try:
        import credentials as creds  # noqa: PLC0415
    except ImportError:
        return {}
    print(
        "WARNING: credentials.py is deprecated — migrate to config.yaml "
        "(see config.yaml.example)",
        file=sys.stderr,
    )
    cfg = {}
    if hasattr(creds, 'username'):
        cfg['username'] = creds.username
    if hasattr(creds, 'password'):
        cfg['password'] = creds.password
    if hasattr(creds, 'download_dir'):
        cfg['download_dir'] = creds.download_dir
    if hasattr(creds, 'tenants'):
        cfg['tenants'] = creds.tenants
    elif hasattr(creds, 'documents_url'):
        url = creds.documents_url
        name = urlparse(url).netloc.split('.')[0]
        cfg['tenants'] = [{'name': name, 'url': url}]
    return cfg


def load_config(argv=None):
    """Return merged config dict. Exits with an error message on bad config."""
    args = _parse_args(argv)

    cfg = dict(DEFAULTS)

    # --- config file ---
    config_path = args.config or os.environ.get('CASAVI_CONFIG', 'config.yaml')
    file_cfg = _load_yaml(config_path, required=bool(args.config))
    cfg.update({k: v for k, v in file_cfg.items() if v is not None})

    # --- legacy fallback (only when no config file was found) ---
    if not file_cfg:
        legacy = _load_legacy_credentials()
        cfg.update({k: v for k, v in legacy.items() if v is not None})

    # --- environment variables ---
    for env_var, key in [
        ('CASAVI_USERNAME', 'username'),
        ('CASAVI_PASSWORD', 'password'),
        ('CASAVI_DOWNLOAD_DIR', 'download_dir'),
    ]:
        val = os.environ.get(env_var)
        if val is not None:
            cfg[key] = val

    tenants_env = os.environ.get('CASAVI_TENANTS')
    if tenants_env:
        try:
            cfg['tenants'] = json.loads(tenants_env)
        except json.JSONDecodeError as exc:
            print(f"ERROR: CASAVI_TENANTS is not valid JSON: {exc}", file=sys.stderr)
            sys.exit(1)

    # --- CLI args ---
    if args.username:
        cfg['username'] = args.username
    if args.password:
        cfg['password'] = args.password
    if args.download_dir:
        cfg['download_dir'] = args.download_dir
    if args.video:
        cfg['video'] = True

    if args.filter_tenants:
        known = {t['name'] for t in cfg.get('tenants', [])}
        unknown = set(args.filter_tenants) - known
        if unknown:
            print(f"ERROR: Unknown tenant(s): {', '.join(sorted(unknown))}", file=sys.stderr)
            print(f"Configured tenants: {', '.join(sorted(known)) or '(none)'}", file=sys.stderr)
            sys.exit(1)
        cfg['tenants'] = [t for t in cfg['tenants'] if t['name'] in args.filter_tenants]

    # --- validation ---
    missing = [k for k in ('username', 'password') if not cfg.get(k)]
    if missing:
        print(f"ERROR: Missing required config: {', '.join(missing)}", file=sys.stderr)
        print(
            "Provide via config.yaml, env vars "
            "(CASAVI_USERNAME / CASAVI_PASSWORD), or --username / --password.",
            file=sys.stderr,
        )
        sys.exit(1)

    if not cfg.get('tenants'):
        print("ERROR: No tenants configured.", file=sys.stderr)
        sys.exit(1)

    return cfg
