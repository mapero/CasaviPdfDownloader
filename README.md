# CasaviPdfDownloader

Download all your PDFs from Casavi automatically.

## Intro

Casavi portals don't offer a bulk download option. This tool automates it by logging in with Playwright (headless Chromium), expanding every folder, and downloading each PDF — skipping files already downloaded in a previous run. Supports multiple tenants (separate Casavi portals).

## Quick start

### Option A — Docker (recommended)

```bash
cp config.yaml.example config.yaml
# edit config.yaml with your credentials and tenant URLs
docker build -t casavi-downloader .
docker run --rm \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  -v $(pwd)/data:/app/DownloadedFiles \
  casavi-downloader
```

### Option B — Local Python

```bash
cp config.yaml.example config.yaml
# edit config.yaml with your credentials and tenant URLs
python run.py
```

`run.py` creates a virtualenv, installs dependencies, and runs the downloader.

## Configuration

Configuration is resolved in order — later sources override earlier ones:

| Priority | Source |
|----------|--------|
| 1 (lowest) | `config.yaml` |
| 2 | Environment variables |
| 3 (highest) | CLI arguments |

### config.yaml

```yaml
username: your@email.com
password: yourpassword

data_dir: ./DownloadedFiles      # state file lives here (default: ./DownloadedFiles)
# download_dir: /mnt/nas/casavi  # PDF files (default: <data_dir>/files)

tenants:
  - name: my-property            # becomes the subfolder name under download_dir
    url: https://portal.example.de/app/c/123456/info/documents
  - name: second-property
    url: https://other.mycasavi.com/app/c/789012/info/documents
```

See `config.yaml.example` for a full template.

### Environment variables

| Variable | Description |
|----------|-------------|
| `CASAVI_USERNAME` | Login email |
| `CASAVI_PASSWORD` | Login password |
| `CASAVI_DATA_DIR` | Directory for `downloaded.yaml` state file |
| `CASAVI_DOWNLOAD_DIR` | Directory for downloaded PDFs (default: `<data_dir>/files`) |
| `CASAVI_CONFIG` | Path to an alternate config file |
| `CASAVI_TENANTS` | JSON array of `{"name","url"}` objects — overrides tenants in config file |

### CLI arguments

```
--config FILE        Path to config.yaml (default: config.yaml)
--username EMAIL
--password PASS
--data-dir DIR       Directory for downloaded.yaml state file
--download-dir DIR   Directory for downloaded PDFs (default: <data-dir>/files)
--tenant NAME        Only process this tenant (repeatable)
--video              Record debug videos to ./debug-videos/
```

## Output

```
<data_dir>/
  downloaded.yaml          ← tracks already-downloaded doc IDs

<download_dir>/            ← default: <data_dir>/files
  <tenant-name>/
    <doc-id>_<filename>.pdf
```

`downloaded.yaml` lets you move PDFs elsewhere (e.g. Paperless-ngx) without them being re-downloaded on the next run. Set `download_dir` independently when you want PDFs on a separate mount.

## Docker examples

```bash
# default layout — state and PDFs under the same volume
docker run --rm \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  -v $(pwd)/data:/app/DownloadedFiles \
  casavi-downloader

# separate volumes for state and PDFs
docker run --rm \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  -v $(pwd)/data:/data \
  -v /mnt/nas/casavi:/downloads \
  -e CASAVI_DATA_DIR=/data \
  -e CASAVI_DOWNLOAD_DIR=/downloads \
  casavi-downloader

# single tenant, credentials via env vars
docker run --rm \
  -e CASAVI_USERNAME=your@email.com \
  -e CASAVI_PASSWORD=secret \
  -e CASAVI_TENANTS='[{"name":"my-property","url":"https://..."}]' \
  -v $(pwd)/data:/app/DownloadedFiles \
  casavi-downloader --tenant my-property

# debug: record video of the browser session
docker run --rm \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  -v $(pwd)/data:/app/DownloadedFiles \
  -v $(pwd)/debug-videos:/app/debug-videos \
  casavi-downloader --video
```
