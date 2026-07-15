# Centuriae

**→ [centuriae.github.io](https://centuriae.github.io/index.html)**

Centuriae is an experiment in loosely structured writing retreats: focused writing time over a weekend, creating space for brilliant people to wrestle with and write down their ideas. At the end of a retreat, everyone submits what they wrote to this site.

This repo generates that site. The point isn't a polished, final anthology — it's **accountability and history**. The site captures where a piece of writing was the moment the weekend ended, git tracks how it got there, and publishing it is a small celebration of one milestone in a longer journey of writing. Rough edges are welcome. Getting the words down is the achievement.

If you want to join a future retreat, [express interest here](https://forms.gle/EwMPciRoT5rSHPNr9).

## Submitting your writing

Your submission is a single Markdown file added to the [`content/`](content/) directory. Each file becomes one post on the site.

### 1. Create your Markdown file

Name it `NN-a-short-slug.md`, where `NN` is the next available number. Look in [`content/`](content/) for the highest number so far and add one (e.g. if the last piece is `36-...`, yours is `37-...`).

Start the file with a frontmatter block, then write your piece below it:

```markdown
---
title: The Title of Your Piece
number: 37
author: Your Name
author_link: https://your-website.example   # optional
retreat: 3
---

Your writing starts here. Standard Markdown works — headings, **bold**,
_italics_, [links](https://example.com), lists, blockquotes, code, and footnotes.
```

Frontmatter fields:

| Field         | Required | Notes                                                                                 |
| ------------- | -------- | ------------------------------------------------------------------------------------- |
| `title`       | yes      | Display title of your post.                                                           |
| `number`      | yes      | Must be unique across all posts — the build fails on duplicates. Match the filename.  |
| `author`      | yes      | Your name, as you'd like it shown.                                                    |
| `author_link` | no       | A URL to link your name to (personal site, socials, etc.).                            |
| `retreat`     | yes      | The retreat this piece belongs to. Use the numeric key from [`config.json`](config.json) (see below). |

### 2. Pick your retreat

The `retreat` field is an index into the `retreats` map in [`config.json`](config.json). For example:

```json
"retreats": {
    "0": "Pilot",
    "1": "6-9 March 2026",
    "2": "8-11 May 2026",
    "3": "10-13 July 2026"
}
```

So `retreat: 3` groups your post under **10-13 July 2026** on the site. If your retreat isn't listed yet, add a new entry to `config.json`.

### 3. Add images (optional)

Put image files in [`content/assets/`](content/assets/), prefixed with your post number, and reference them with a relative `assets/` path:

```markdown
<img class="imagecenter" src="assets/37-my-diagram.png" alt="A short description" style="max-width: 420px;">
<p class="caption">An optional caption.</p>
```

### 4. Attach a PDF (optional)

To link a PDF, drop the file somewhere in the repo and add a marker comment where you want the link to appear:

```markdown
<!-- PDF: assets/37-my-essay.pdf -->
```

This renders as a small "Open PDF ↗" link.

### 5. Fork, commit, and open a pull request

Submissions come in as pull requests from your own fork:

1. **Fork** this repo to your own GitHub account.
2. **Clone** your fork and add your Markdown file (and any assets) as described above.
3. **Commit** your work — ideally in several commits as you draft, so the timeline reflects your process (see below).
4. **Push** to your fork and **open a pull request** against `main` on this repo.

Once your PR is merged, a GitHub Action rebuilds the site and deploys it automatically — no manual publishing step.

> **Why commit history matters:** every post has a **"View Timeline"** link built from its git history, showing how the writing evolved commit by commit. If you commit your drafts as you go, that journey becomes part of the site. This is the "history over polish" idea in action — so commit early, commit often, and don't be shy about messy intermediate states.

## Running the site locally

You'll need Python 3. A virtual environment is recommended.

```bash
# from the repo root
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**Build the site** into the `_build/` directory:

```bash
python3 build.py
```

**Build and serve** with a live local server:

```bash
python3 serve.py            # serves at http://localhost:8000
python3 serve.py 8080       # or pass a port; it auto-increments if taken
```

`serve.py` runs the build first, then serves `_build/`. Re-run it after editing content to see your changes. The generated `_build/` directory is not committed — it's produced fresh on every build.

> **Note:** the "View Timeline" diff pages are generated from git history, so they only populate for files that have been committed. A brand-new, uncommitted post will still render fine locally.

## Repo layout

| Path                | What it is                                                            |
| ------------------- | -------------------------------------------------------------------- |
| `content/`          | The posts — one Markdown file per submission, plus an `assets/` dir. |
| `config.json`       | Site title, footer, and the retreat list.                           |
| `intro.md`          | The intro blurb shown at the top of the index page.                 |
| `build.py`          | The static site generator.                                          |
| `serve.py`          | Local build-and-serve helper.                                       |
| `templates/`        | HTML templates for pages and diff timelines.                        |
| `css/`, `js/`, `static/` | Styling and client-side assets.                                |
| `_build/`           | Generated output (gitignored).                                      |

---

A project by [Callum Rhys Tilbury](https://callum.tilbury.co.za) — trying to be a reformed _Ideas Guy_, biased towards action.
