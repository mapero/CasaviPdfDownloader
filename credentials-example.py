# Howto
# - copy this file to credentials.py
# - add your username and password
# - add one entry per Casavi tenant to the tenants list
# - run: myenv/bin/python download.py

# Credentials (shared across all tenants)
username = 'your@email.com'
password = 'yourpassword'

# Tenants — add one dict per Casavi portal you want to download from.
# 'name' becomes the subfolder under download_dir.
# The login URL is derived automatically from the portal domain.
tenants = [
    {
        'name': 'my-property',
        'url': 'https://portal.example.de/app/c/123456/info/documents',
    },
    {
        'name': 'second-property',
        'url': 'https://other.mycasavi.com/app/c/789012/info/documents',
    },
]

download_dir = './DownloadedFiles'  # PDFs saved to <download_dir>/<tenant_name>/
