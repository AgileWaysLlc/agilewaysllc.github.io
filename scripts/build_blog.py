#!/usr/bin/env python3
"""
Builds the AgileWays site into ./build:
  - copies every static file (index.html, about.html, services.html,
    404.html, assets/) as-is
  - converts every posts/*.md file into build/blog/<slug>/index.html
  - regenerates build/blog.html with a list of all posts, newest first

Usage: python scripts/build_blog.py
Requires: markdown  (see requirements.txt)
"""
import shutil
import re
import time
import stat
from pathlib import Path
from datetime import datetime

import markdown

ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "posts"
TEMPLATES_DIR = ROOT / "templates"
BUILD_DIR = ROOT / "build"

STATIC_FILES = ["index.html", "about.html", "services.html", "404.html"]
STATIC_DIRS = ["assets"]


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def parse_frontmatter(raw_text: str):
    """Parses a simple '---\\nkey: value\\n---\\nbody' block.
    Values can optionally be wrapped in quotes. No nested/list values needed
    for this site, so a full YAML parser is unnecessary."""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw_text, re.DOTALL)
    if not match:
        return {}, raw_text

    fm_block, body = match.groups()
    meta = {}
    for line in fm_block.splitlines():
        if not line.strip() or ":" not in line:
            continue
        key, _, value = line.partition(":")
        value = value.strip().strip('"').strip("'")
        meta[key.strip()] = value
    return meta, body


def load_posts():
    posts = []
    if not POSTS_DIR.exists():
        return posts

    for md_file in sorted(POSTS_DIR.glob("*.md")):
        meta, body = parse_frontmatter(md_file.read_text())

        title = meta.get("title", md_file.stem)
        date_raw = meta.get("date")
        if date_raw:
            date = datetime.strptime(date_raw, "%Y-%m-%d")
        else:
            date = datetime.fromtimestamp(md_file.stat().st_mtime)

        slug = meta.get("slug") or slugify(title)
        summary = meta.get("summary", "")

        html_body = markdown.markdown(
            body,
            extensions=["fenced_code", "tables", "toc"],
        )

        posts.append(
            {
                "title": title,
                "date": date,
                "slug": slug,
                "summary": summary,
                "content": html_body,
            }
        )

    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


def format_date(date: datetime) -> str:
    """Cross-platform 'Month D, YYYY' formatting (%-d isn't supported on Windows)."""
    return f"{date.strftime('%B')} {date.day}, {date.year}"


def render_post(post, template):
    return (
        template.replace("{{title}}", post["title"])
        .replace("{{summary}}", post["summary"])
        .replace("{{date_display}}", format_date(post["date"]))
        .replace("{{content}}", post["content"])
    )


def render_index(posts, template):
    if not posts:
        list_html = '<p class="empty-state">No posts yet — check back soon.</p>'
    else:
        items = []
        for p in posts:
            items.append(
                f'''<li>
  <a href="/blog/{p["slug"]}/">
    <h3>{p["title"]}</h3>
    <p>{p["summary"]}</p>
  </a>
  <time datetime="{p["date"].strftime("%Y-%m-%d")}">{format_date(p["date"])}</time>
</li>'''
            )
        list_html = '<ul class="post-list">\n' + "\n".join(items) + "\n</ul>"

    return template.replace("{{post_list}}", list_html)


def _remove_readonly(func, path, exc_info):
    """shutil.rmtree onerror handler: clears the read-only bit and retries.
    Needed on Windows, where files can end up read-only after being
    synced by OneDrive/Dropbox."""
    Path(path).chmod(stat.S_IWRITE)
    func(path)


def clean_build_dir():
    """Removes the build directory, retrying briefly on Windows/OneDrive
    file locks (PermissionError) before giving up with a clear message."""
    if not BUILD_DIR.exists():
        BUILD_DIR.mkdir(parents=True)
        return

    attempts = 5
    for attempt in range(1, attempts + 1):
        try:
            shutil.rmtree(BUILD_DIR, onerror=_remove_readonly)
            break
        except PermissionError:
            if attempt == attempts:
                raise SystemExit(
                    "\nCouldn't delete the build/ folder — something still has "
                    "a file inside it open.\n"
                    "Things to check:\n"
                    "  - Stop any local server (e.g. `python -m http.server`) "
                    "before rebuilding\n"
                    "  - If this folder is inside OneDrive/Dropbox, wait a "
                    "moment for sync to finish, or pause syncing\n"
                    "  - Close any editor or file explorer window with a "
                    "file from build/ open\n"
                    "Then run the build again."
                )
            time.sleep(0.5)

    BUILD_DIR.mkdir(parents=True)


def main():
    clean_build_dir()

    # 1. copy hand-written static pages and assets as-is
    for name in STATIC_FILES:
        src = ROOT / name
        if src.exists():
            shutil.copy2(src, BUILD_DIR / name)
    for name in STATIC_DIRS:
        src = ROOT / name
        if src.exists():
            shutil.copytree(src, BUILD_DIR / name)

    # 2. build blog posts
    posts = load_posts()
    post_template = (TEMPLATES_DIR / "post.html").read_text()
    blog_dir = BUILD_DIR / "blog"
    blog_dir.mkdir(exist_ok=True)

    for post in posts:
        out_dir = blog_dir / post["slug"]
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "index.html").write_text(render_post(post, post_template))
        print(f"  built post: /blog/{post['slug']}/")

    # 3. build blog index
    index_template = (TEMPLATES_DIR / "blog-index.html").read_text()
    (BUILD_DIR / "blog.html").write_text(render_index(posts, index_template))
    print(f"  built blog index with {len(posts)} post(s)")

    print(f"\nDone. Site built to {BUILD_DIR}")


if __name__ == "__main__":
    main()
