import re
import requests

# URLs
url1 = 'https://sportlink-playlist.pages.dev/zio.m3u'
url2 = 'https://premiumplugx.me/vzy/playlist.php'


def parse_m3u(content):
  lines = content.splitlines()
  entries = []
  i = 0
  while i < len(lines):
    line = lines[i].strip()
    if line.startswith('#EXTINF:'):
      extinf = line
      url_line = ''
      if i + 1 < len(lines):
        url_line = lines[i + 1].strip()
        i += 1
      entries.append({'extinf': extinf, 'url': url_line})
    i += 1
  return entries


new_entries = []

# --- 1. Process Source 1 (Only Star Sports, Group: Sports, Title suffix: [Jio Tv]) ---
try:
  resp1 = requests.get(url1, timeout=30)
  if resp1.status_code == 200:
    entries1 = parse_m3u(resp1.text)
    for entry in entries1:
      extinf = entry['extinf']
      url = entry['url']

      match = re.search(r'(#EXTINF:[^,]*),(.*)', extinf)
      if match:
        attrs = match.group(1)
        title = match.group(2).strip()

        if 'star sports' in title.lower():
          # Update group-title to Sports
          if 'group-title=' in attrs:
            attrs = re.sub(
                r'group-title="[^"]*"', 'group-title="Sports"', attrs
            )
          else:
            attrs += ' group-title="Sports"'

          # Append [Jio Tv] to title
          new_title = title + ' [Jio Tv]'
          new_entries.append({'extinf': f'{attrs},{new_title}', 'url': url})
except Exception as e:
  print(f'Error fetching source 1: {e}')

# --- 2. Process Source 2 (Keep others same, 9x -> Music, Big Magic -> Entertainment) ---
try:
  resp2 = requests.get(url2, timeout=30)
  if resp2.status_code == 200:
    entries2 = parse_m3u(resp2.text)
    for entry in entries2:
      extinf = entry['extinf']
      url = entry['url']

      match = re.search(r'(#EXTINF:[^,]*),(.*)', extinf)
      if match:
        attrs = match.group(1)
        title = match.group(2).strip()

        # 9x channels in Music group
        if '9x' in title.lower():
          if 'group-title=' in attrs:
            attrs = re.sub(r'group-title="[^"]*"', 'group-title="Music"', attrs)
          else:
            attrs += ' group-title="Music"'
        # Big Magic channels in Entertainment group
        elif 'big magic' in title.lower():
          if 'group-title=' in attrs:
            attrs = re.sub(
                r'group-title="[^"]*"', 'group-title="Entertainment"', attrs
            )
          else:
            attrs += ' group-title="Entertainment"'

        new_entries.append({'extinf': f'{attrs},{title}', 'url': url})
except Exception as e:
  print(f'Error fetching source 2: {e}')

# --- Build Final M3U File ---
output_lines = ['#EXTM3U']
for entry in new_entries:
  output_lines.append(entry['extinf'])
  output_lines.append(entry['url'])

with open('playlist.m3u', 'w', encoding='utf-8') as f:
  f.write('\n'.join(output_lines))

print(
    f'Playlist generated successfully with {len(new_entries)} total channels.'
)
