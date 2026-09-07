"""Give every sitemap URL a <lastmod> Google can trust.

Why this exists. On 2026-09-07 the Search Console URL Inspection API reported
every sampled tashbetz page as "Crawled - currently not indexed", with
Googlebot's last crawl of this host dated 2026-08-11. Several deploys shipped
after that date and Google fetched none of them. The sitemap listed 6,071 URLs
with a <loc> and nothing else, so it carried no signal about which pages had
changed since Google last looked.

The hard part is not emitting the tag, it is emitting a date that is TRUE.
Seeding all 6,071 URLs with the build date would claim the whole corpus changed
at once, which is false and teaches Google to ignore the field. The generated
HTML under docs/ is committed, so git already knows when each page last really
changed, and that is what this module reads.
"""
import datetime
import functools
import os
import subprocess
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _candidate(rel):
    return os.path.join('docs', rel, 'index.html').replace(os.sep, '/') \
        if rel else 'docs/index.html'


def page_path(url_path):
    """Repo-relative path of the built file that serves a sitemap URL path.

    The corpus mixes two directory conventions and both are real on disk:
    /milon/e/ and /milon/w/ keep the percent-encoded name
    ('docs/milon/e/%D7%90%D7%99%D7%9C%D7%AA/'), while the letter pages keep the
    raw Hebrew one ('docs/milon/actor-letter-<alef>/'). Resolve against disk
    rather than guessing, since guessing wrong silently dates a page today and
    that is exactly the untrustworthy lastmod this module exists to avoid.
    """
    literal = _candidate(url_path.strip('/'))
    if os.path.exists(os.path.join(ROOT, literal)):
        return literal
    decoded = _candidate(urllib.parse.unquote(url_path).strip('/'))
    if os.path.exists(os.path.join(ROOT, decoded)):
        return decoded
    return literal


@functools.lru_cache(maxsize=1)
def _history():
    """path -> ISO date of the commit that last touched it, for all of docs/.

    One `git log` pass, newest commit first, so the first time a path appears
    is its last modification. Cheap enough (well under a second) to do once.
    """
    # core.quotePath=false is load-bearing: by default git escapes non-ASCII
    # paths ("docs/milon/actor-letter-\327\220/..."), which silently misses the
    # 262 letter pages whose directories carry raw Hebrew, and drops them onto
    # the today fallback.
    out = subprocess.run(
        ['git', '-c', 'core.quotePath=false', 'log',
         '--format=__%cI', '--name-only', '--', 'docs'],
        cwd=ROOT, capture_output=True, text=True).stdout
    dates, day = {}, None
    for line in out.splitlines():
        if line.startswith('__'):
            day = line[2:12]
        elif line and day and line not in dates:
            dates[line] = day
    return dates


@functools.lru_cache(maxsize=1)
def _dirty():
    """Files under docs/ the working tree has changed since the last commit.

    A generator rewrites its pages and only then are they committed, so at
    build time git history still holds the PREVIOUS date for a page that just
    changed. Without this the sitemap would understate freshness on exactly
    the pages a rebuild touched, which is the case lastmod exists to signal.
    """
    out = subprocess.run(
        ['git', '-c', 'core.quotePath=false', 'status', '--porcelain', '--', 'docs'],
        cwd=ROOT, capture_output=True, text=True).stdout
    return {line[3:].strip('"') for line in out.splitlines() if len(line) > 3}


def git_dates(paths):
    """The subset of `paths` that git has a date for."""
    hist = _history()
    return {p: hist[p] for p in paths if p in hist}


def dates_for(paths):
    """A date for every path.

    Changed-but-uncommitted and never-seen files are dated today; everything
    else takes the date of the commit that last touched it.
    """
    hist, dirty = _history(), _dirty()
    today = datetime.date.today().isoformat()
    return {p: today if p in dirty else hist.get(p, today) for p in paths}


def url_entry(base, url_path, date):
    return f'  <url><loc>{base}{url_path}</loc><lastmod>{date}</lastmod></url>\n'


def entries(base, url_paths):
    """Rendered <url> lines for url_paths, in the order given."""
    dates = dates_for([page_path(u) for u in url_paths])
    return ''.join(url_entry(base, u, dates[page_path(u)]) for u in url_paths)
