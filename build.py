import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from string import Template

import markdown

# Configuration
CONTENT_DIR = Path('content')
OUTPUT_DIR = Path('_build')
TEMPLATE_DIR = Path('templates')
CSS_DIR = Path('css')
CONFIG_FILE = Path('config.json')
STATIC_DIR = Path('static')

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def get_git_info(filepath):
    """Extracts author, date, and commit hash from git for a given file."""
    try:
        cmd_log = ['git', 'log', '-1', '--format=%an|%ad|%h', '--date=short', '--', str(filepath)]
        result_log = subprocess.run(cmd_log, capture_output=True, text=True, check=True)
        
        if not result_log.stdout.strip():
            return {'author': 'Unknown', 'date': 'Draft', 'hash': 'N/A'}
            
        author, date, commit_hash = result_log.stdout.strip().split('|')

        return {
            'author': author, 
            'date': date, 
            'hash': commit_hash
        }
    except subprocess.CalledProcessError:
        return {'author': 'Unknown', 'date': 'Error', 'hash': 'N/A'}
    except Exception as e:
        return {'author': 'Error', 'date': 'Error', 'hash': 'N/A'}

def get_file_history(filepath):
    """Extracts the full git history and content of a file."""
    try:
        cmd = ['git', 'log', '--follow', '--pretty=format:%h|%ad|%s', '--date=iso-strict', '--', str(filepath)]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        revisions = []
        for line in result.stdout.strip().split('\n'):
            if not line: continue
            h, d, s = line.split('|', 2)
            
            try:
                content_cmd = ['git', 'show', f'{h}:{filepath}']
                content_result = subprocess.run(content_cmd, capture_output=True, text=True, check=True)
                revisions.append({
                    'hash': h,
                    'date': d,
                    'subject': s,
                    'content': content_result.stdout,
                    'filename': filepath.name
                })
            except subprocess.CalledProcessError:
                continue
                
        return revisions
    except Exception as e:
        print(f"Error getting history for {filepath}: {e}")
        return []

def generate_pdf_link(pdf_path):
    """Generate a small unobtrusive 'Open PDF' link."""
    return f'<p class="pdf-link"><a href="{pdf_path}" target="_blank" rel="noopener noreferrer">Open PDF ↗</a></p>'


def process_pdf_markers(content):
    """Process <!-- PDF: path/to/file.pdf --> markers and replace with a small link."""
    import re

    pattern = r"<!-- PDF:\s*([^\s]+)\s*-->"

    def replace_marker(match):
        pdf_path = match.group(1)
        return generate_pdf_link(pdf_path)

    return re.sub(pattern, replace_marker, content)


def build():
    # Prepare output directory
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir()
    (OUTPUT_DIR / 'posts').mkdir()
    (OUTPUT_DIR / '.nojekyll').touch()

    # Load Config
    config = load_config()
    site_title_val = config.get('site_title', 'Centuriae')
    site_title_upper = site_title_val.upper()
    retreats_map = config.get('retreats', {})

    # Process footer markdown
    footer_text_raw = config.get('footer_text', '')
    footer_html = markdown.markdown(footer_text_raw.strip()) if footer_text_raw else ""

    intro_file = Path('intro.md')
    intro_html = markdown.markdown(intro_file.read_text().strip()) if intro_file.exists() else ""

    # Copy Assets
    shutil.copy(CSS_DIR / 'style.css', OUTPUT_DIR / 'style.css')
    shutil.copy(CSS_DIR / 'diff.css', OUTPUT_DIR / 'diff.css')
    
    JS_DIR = Path('js')
    if JS_DIR.exists():
        (OUTPUT_DIR / 'js').mkdir(exist_ok=True)
        for js_file in JS_DIR.glob('*.js'):
            shutil.copy(js_file, OUTPUT_DIR / 'js' / js_file.name)

    # Copy Static Assets
    if STATIC_DIR.exists():
        for static_file in STATIC_DIR.glob('*'):
            if static_file.is_file():
                shutil.copy(static_file, OUTPUT_DIR / static_file.name)

    # Copy local images and assets
    # 1. Copy 'assets' directory if it exists
    if (CONTENT_DIR / 'assets').exists():
        shutil.copytree(CONTENT_DIR / 'assets', OUTPUT_DIR / 'assets', dirs_exist_ok=True)
        shutil.copytree(CONTENT_DIR / 'assets', OUTPUT_DIR / 'posts' / 'assets', dirs_exist_ok=True)

    # 2. Copy images at the root of content (maintain existing behavior for root images)
    image_extensions = ['*.png', '*.jpg', '*.jpeg', '*.gif', '*.webp', '*.svg', '*.ico']
    for ext in image_extensions:
        for img_file in CONTENT_DIR.glob(ext):
            shutil.copy(img_file, OUTPUT_DIR / img_file.name)
            shutil.copy(img_file, OUTPUT_DIR / 'posts' / img_file.name)

    # Load Templates
    with open(TEMPLATE_DIR / 'layout.html', 'r') as f:
        layout_template = Template(f.read())
        
    with open(TEMPLATE_DIR / 'diff.html', 'r') as f:
        diff_template = Template(f.read())

    all_posts = []

    # 1. Collect Metadata
    for md_file in sorted(CONTENT_DIR.glob('*.md')):
        with open(md_file, 'r') as f:
            text = f.read()

        md = markdown.Markdown(
            extensions=["meta", "fenced_code", "codehilite", "footnotes", "pymdownx.arithmatex"],
            extension_configs={"pymdownx.arithmatex": {"generic": True}},
        )
        html_content = md.convert(text)
        html_content = process_pdf_markers(html_content)
        meta = md.Meta if hasattr(md, 'Meta') else {}
        
        title = meta.get('title', [md_file.stem.replace('-', ' ').title()])[0]
        number = meta.get('number', [None])[0]
        if not number:
            prefix = md_file.stem.split('-')[0]
            number = prefix if prefix.isdigit() else None

        # Determine slug for permalink - use number if available, else filename
        slug = number if number else md_file.stem

        author_name = meta.get('author', [None])[0]
        author_link = meta.get('author_link', [None])[0]
        retreat_index = meta.get('retreat', [None])[0]

        git_info = get_git_info(md_file)

        all_posts.append({
            'md_file': md_file,
            'slug': slug,
            'title': title,
            'number': number,
            'author_name': author_name,
            'author_link': author_link,
            'retreat_index': retreat_index,
            'git_info': git_info,
            'html_content': html_content,
            'date': git_info['date']
        })

    # Validate unique numbers
    numbers = [p['number'] for p in all_posts if p['number'] is not None]
    if len(numbers) != len(set(numbers)):
        duplicates = [x for x in numbers if numbers.count(x) > 1]
        raise ValueError(f"Duplicate post numbers found: {set(duplicates)}")

    # 2. Sort Posts
    def sort_key(p):
        if p['number'] is not None:
            return (0, int(p['number']))
        return (1, p['date'])
    all_posts.sort(key=sort_key)

    # 3. Render Posts
    for i, post in enumerate(all_posts):
        print(f"Rendering {post['slug']}...")
        
        # Calculate Navigation
        prev_post = all_posts[i-1] if i > 0 else None
        next_post = all_posts[i+1] if i < len(all_posts) - 1 else None
        
        nav_html = '<hr class="post-divider">'
        if prev_post or next_post:
            nav_html += '<div class="post-nav">'
            if prev_post:
                nav_html += f"<a href='{prev_post['slug']}.html' style='text-decoration: none;'>&larr; {prev_post['title']}</a>"
            else:
                nav_html += "<span></span>"
                
            if next_post:
                nav_html += f"<a href='{next_post['slug']}.html' style='text-decoration: none;'>{next_post['title']} &rarr;</a>"
            else:
                nav_html += "<span></span>"
            nav_html += '</div>'

        # Resolve Commit/Timeline Link
        commit_hash = post['git_info']['hash']
        if commit_hash not in ['N/A', 'Draft', 'Error']:
            timeline_link = f"<a href='../diffs/{post['slug']}.html?commit={commit_hash}' style='color: inherit; text-decoration: underline; text-decoration-color: var(--border-color);'>View Timeline</a>"
            commit_display = timeline_link
        else:
            commit_display = commit_hash

        final_author = post['author_name'] if post['author_name'] else post['git_info']['author']
        author_display = f"<a href='{post['author_link']}' target='_blank' rel='noopener noreferrer' style='color: inherit; text-decoration: underline; text-decoration-color: var(--border-color);'>{final_author}</a>" if post['author_link'] else final_author

        num_display = f"<span style='font-family: var(--font-mono);'>{post['number']}</span> &nbsp; | &nbsp; " if post['number'] else ""
        meta_html = f"{num_display}By {author_display} &nbsp; | &nbsp; Last updated: {post['git_info']['date']} &nbsp; | &nbsp; {commit_display}"
        
        # Render main HTML
        final_html = layout_template.safe_substitute(
            title=post['title'],
            content=post['html_content'],
            nav=nav_html,
            meta=meta_html,
            site_title=site_title_val,
            footer_text=footer_html,
            root_path='..'
        )
        
        with open(OUTPUT_DIR / 'posts' / f"{post['slug']}.html", 'w') as f:
            f.write(final_html)

        # Render Diff Page
        history = get_file_history(post['md_file'])
        diff_dir = OUTPUT_DIR / 'diffs'
        diff_dir.mkdir(exist_ok=True)
        
        diff_html = diff_template.safe_substitute(
            title=post['title'],
            post_url=f"../posts/{post['slug']}.html",
            history_json=json.dumps(history),
            site_title=site_title_val,
            author_display=author_display,
            post_number=post['number'] if post['number'] else "",
            footer_text=footer_html
        )
        with open(diff_dir / f"{post['slug']}.html", 'w') as f:
            f.write(diff_html)

    # 4. Render Index
    # Group posts by retreat, then sort retreats in descending order (newest first).
    # Within each retreat, posts stay in ascending order.
    from itertools import groupby

    def retreat_sort_key(p):
        r = p['retreat_index']
        try:
            return int(r) if r is not None else -1
        except (ValueError, TypeError):
            return -1

    posts_by_retreat = {}
    for post in all_posts:
        r = post['retreat_index']
        posts_by_retreat.setdefault(r, []).append(post)

    sorted_retreat_keys = sorted(
        posts_by_retreat.keys(),
        key=lambda r: (int(r) if r is not None and str(r).lstrip('-').isdigit() else -1),
        reverse=True
    )

    intro_block = f'<div class="index-intro">{intro_html}</div>' if intro_html else ""

    import re

    def slugify(text):
        text = text.lower()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[\s_]+', '-', text)
        return re.sub(r'-+', '-', text).strip('-')

    index_list_items = ""
    for retreat_key in sorted_retreat_keys:
        retreat_label = retreats_map.get(str(retreat_key), f"Retreat {retreat_key}") if retreat_key is not None else ""
        if retreat_label:
            anchor_id = slugify(retreat_label)
            index_list_items += f"""
        <li class="retreat-divider-item" id="{anchor_id}">
            <div class="retreat-divider"><span class="retreat-label"><a href="#{anchor_id}" class="retreat-label-link">{retreat_label}</a></span></div>
        </li>"""

        for post in sorted(posts_by_retreat[retreat_key], key=lambda p: int(p['number']) if p['number'] and str(p['number']).isdigit() else 0, reverse=True):
            author_html = f"<a href='{post['author_link']}' target='_blank' rel='noopener noreferrer'>{post['author_name'] if post['author_name'] else post['git_info']['author']}</a>" if post['author_link'] else (post['author_name'] if post['author_name'] else post['git_info']['author'])
            index_list_items += f"""
        <li>
            <span class='post-number'>{post['number'] if post['number'] else ''}</span><div class='index-entry'><a href='posts/{post['slug']}.html'>{post['title']}</a><span class='author-meta'>{author_html}</span></div>
        </li>"""

    index_content = f"""
    <div style="max-width: 600px; margin: 2rem auto;">
        {intro_block}
        <ul class="index-posts">
            {index_list_items}
        </ul>
    </div>
    """
    
    # Use layout template for index too
    final_index = layout_template.safe_substitute(
        title=site_title_val,
        content=index_content,
        meta="",
        site_title=site_title_val,
        header_prefix="",
        footer_text=footer_html,
        root_path='.',
        nav=""
    )
    
    # Patch index template to hide the standard header if meta is empty
    # Or just use the original logic of cutting it
    if not (OUTPUT_DIR / 'index.html').exists() or True:
        header_block = '            <header class="post-header">\n                ${header_prefix}\n                <h1>${title}</h1>\n                <div class="meta">${meta}</div>\n            </header>'
        # Need to be careful with exact match for replacement
        # Let's adjust layout.html first to make it easier
        pass

    with open(OUTPUT_DIR / 'index.html', 'w') as f:
         f.write(final_index.replace('<header class="post-header">', '<header class="post-header" style="display:none">'))

    print("Build complete!")

if __name__ == "__main__":
    build()
