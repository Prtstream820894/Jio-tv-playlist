import os
import re
import requests
from playwright.sync_api import sync_playwright

url1 = ""
url2 = "https://premiumplugx.me/vzy/playlist.php"


def parse_m3u_blocks(content):
  lines = content.splitlines()
  blocks = []
  i = 0
  n = len(lines)

  while i < n:
    line = lines[i].strip()
    if line.startswith('#EXTINF:'):
      extinf = line
      extra_lines = []
      i += 1
      # Collect intermediate lines (like #KODIPROP, etc.) until URL is found
      while i < n and lines[i].strip().startswith('#'):
        extra_lines.append(lines[i].strip())
        i += 1

      url = lines[i].strip() if i < n else ''
      blocks.append({'extinf': extinf, 'extra': extra_lines, 'url': url})
    i += 1
  return blocks


def get_source2_with_playwright(url):
  print(f'Opening {url} using Playwright Headless Browser...')
  try:
    with sync_playwright() as p:
      browser = p.chromium.launch(
          headless=True,
          args=[
              '--no-sandbox',
              '--disable-setuid-sandbox',
              '--disable-blink-features=AutomationControlled',
          ],
      )
      context = browser.new_context(
          user_agent=(
              'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
              ' (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
          )
      )
      page = context.new_page()

      # Navigate to the playlist URL
      response = page.goto(url, wait_until='networkidle', timeout=60000)

      # Extract full text/source of the page
      content = page.content()
      # Clean up HTML tags if browser wrapped text in <body>/pre tags
      text_content = page.evaluate('document.body.innerText')

      browser.close()

      if '#EXTINF' in text_content:
        print('Successfully extracted M3U content via Playwright!')
        return text_content
      elif '#EXTINF' in content:
        print('Successfully extracted M3U content from raw body!')
        return content
      else:
        print(
            'Playwright opened the page but #EXTINF tags were not found.'
            ' Previewing snippet:'
        )
        print(text_content[:200])
        return text_content
  except Exception as e:
    print(f'Playwright error: {e}')
    return ''


new_blocks = []

# --- 1. Process Source 1 (Star Sports Only) ---
try:
  print('Fetching Source 1...')
  resp1 = requests.get(url1, timeout=30)
  if resp1.status_code == 200:
    blocks1 = parse_m3u_blocks(resp1.text)
    print(f'Source 1 total parsed items: {len(blocks1)}')

    count1 = 0
    for b in blocks1:
      extinf = b['extinf']
      if ',' in extinf:
        header_part, title = extinf.split(',', 1)

        if re.search(r'star\s*sports', title, re.IGNORECASE):
          if 'group-title=' in header_part:
            header_part = re.sub(
                r'group-title="[^"]*"', 'group-title="Sports"', header_part
            )
          else:
            header_part += ' group-title="Sports"'

          clean_title = title.strip()
          if not clean_title.endswith('[Jio Tv]'):
            clean_title = f'{clean_title} [Jio Tv]'

          new_extinf = f'{header_part},{clean_title}'
          new_blocks.append(
              {'extinf': new_extinf, 'extra': b['extra'], 'url': b['url']}
          )
          count1 += 1
    print(f'Source 1 Star Sports added: {count1}')
  else:
    print(f'Source 1 status code: {resp1.status_code}')
except Exception as e:
  print(f'Error Source 1: {e}')

# --- 2. Process Source 2 (Via Playwright Browser) ---
source2_content = get_source2_with_playwright(url2)

# Fallback: Check requests if playwright fails
if not source2_content or '#EXTINF' not in source2_content:
  try:
    print('Trying standard HTTP request fallback for Source 2...')
    r2 = requests.get(
        url2,
        headers={
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0'
            )
        },
        timeout=30,
    )
    if r2.status_code == 200:
      source2_content = r2.text
  except Exception as e:
    print(f'Standard request error: {e}')

if source2_content and '#EXTINF' in source2_content:
  blocks2 = parse_m3u_blocks(source2_content)
  print(f'Source 2 total parsed items: {len(blocks2)}')

  count2 = 0
  for b in blocks2:
    extinf = b['extinf']
    if ',' in extinf:
      header_part, title = extinf.split(',', 1)
      clean_title = title.strip()

      # Rule for 9x -> Music
      if re.search(r'\b9x\b', clean_title, re.IGNORECASE):
        if 'group-title=' in header_part:
          header_part = re.sub(
              r'group-title="[^"]*"', 'group-title="Music"', header_part
          )
        else:
          header_part += ' group-title="Music"'

      # Rule for Big Magic -> Entertainment
      elif re.search(r'big\s*magic', clean_title, re.IGNORECASE):
        if 'group-title=' in header_part:
          header_part = re.sub(
              r'group-title="[^"]*"', 'group-title="Entertainment"', header_part
          )
        else:
          header_part += ' group-title="Entertainment"'

      new_extinf = f'{header_part},{clean_title}'
      new_blocks.append(
          {'extinf': new_extinf, 'extra': b['extra'], 'url': b['url']}
      )
      count2 += 1
  print(f'Source 2 channels added: {count2}')
else:
  print('Error: Could not extract valid M3U data from Source 2.')

# --- Output Final M3U File ---
output_lines = ['#EXTM3U']
for b in new_blocks:
  output_lines.append(b['extinf'])
  for ex in b['extra']:
    output_lines.append(ex)
  output_lines.append(b['url'])

with open('playlist.m3u', 'w', encoding='utf-8') as f:
  f.write('\n'.join(output_lines))

print(f'Done! Saved {len(new_blocks)} total channels in playlist.m3u')
