import re
import requests

url1 = "https://sportlink-playlist.pages.dev/zio.m3u"
url2 = "https://premiumplugx.me/vzy/playlist.php"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def parse_m3u(content):
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    entries = []
    i = 0
    while i < len(lines):
        if lines[i].startswith('#EXTINF:'):
            extinf = lines[i]
            i += 1
            # Skip extra tags like #EXTVLCOPT if present
            while i < len(lines) and lines[i].startswith('#'):
                i += 1
            if i < len(lines):
                url = lines[i]
                entries.append({'extinf': extinf, 'url': url})
        i += 1
    return entries

new_entries = []

# --- 1. Process Source 1 (Star Sports Channels) ---
try:
    print("Fetching Source 1...")
    resp1 = requests.get(url1, headers=headers, timeout=30)
    if resp1.status_code == 200:
        entries1 = parse_m3u(resp1.text)
        print(f"Source 1 total parsed items: {len(entries1)}")
        
        count1 = 0
        for entry in entries1:
            extinf = entry['extinf']
            url = entry['url']

            # Extract title after comma
            if ',' in extinf:
                header_part, title = extinf.split(',', 1)
                
                # Check for Star Sports (case-insensitive)
                if re.search(r'star\s*sports', title, re.IGNORECASE):
                    # Replace or Add group-title="Sports"
                    if 'group-title=' in header_part:
                        header_part = re.sub(r'group-title="[^"]*"', 'group-title="Sports"', header_part)
                    else:
                        header_part += ' group-title="Sports"'
                    
                    new_title = f"{title.strip()} [Jio Tv]"
                    new_entries.append({'extinf': f"{header_part},{new_title}", 'url': url})
                    count1 += 1
        print(f"Source 1 Star Sports added: {count1}")
    else:
        print(f"Source 1 returned status code: {resp1.status_code}")
except Exception as e:
    print(f"Error in Source 1: {e}")

# --- 2. Process Source 2 (All Channels + 9X & Big Magic Grouping) ---
try:
    print("Fetching Source 2...")
    resp2 = requests.get(url2, headers=headers, timeout=30)
    if resp2.status_code == 200:
        entries2 = parse_m3u(resp2.text)
        print(f"Source 2 total parsed items: {len(entries2)}")
        
        count2 = 0
        for entry in entries2:
            extinf = entry['extinf']
            url = entry['url']

            if ',' in extinf:
                header_part, title = extinf.split(',', 1)
                title = title.strip()

                # Grouping rule for 9x
                if re.search(r'\b9x\b', title, re.IGNORECASE):
                    if 'group-title=' in header_part:
                        header_part = re.sub(r'group-title="[^"]*"', 'group-title="Music"', header_part)
                    else:
                        header_part += ' group-title="Music"'
                
                # Grouping rule for Big Magic
                elif re.search(r'big\s*magic', title, re.IGNORECASE):
                    if 'group-title=' in header_part:
                        header_part = re.sub(r'group-title="[^"]*"', 'group-title="Entertainment"', header_part)
                    else:
                        header_part += ' group-title="Entertainment"'

                new_entries.append({'extinf': f"{header_part},{title}", 'url': url})
                count2 += 1
        print(f"Source 2 channels added: {count2}")
    else:
        print(f"Source 2 returned status code: {resp2.status_code}")
except Exception as e:
    print(f"Error in Source 2: {e}")

# --- Write Final Output ---
output_lines = ["#EXTM3U"]
for entry in new_entries:
    output_lines.append(entry['extinf'])
    output_lines.append(entry['url'])

with open('playlist.m3u', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output_lines))

print(f"Final playlist.m3u generated successfully with {len(new_entries)} total channels.")
