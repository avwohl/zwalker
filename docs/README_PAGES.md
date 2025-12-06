# ZWalker GitHub Pages

This directory contains the GitHub Pages website for ZWalker.

## Pages

- **index.html** - Main landing page with overview, stats, and test results
- **GAME_SOURCES.html** - Complete index of 100+ games with download URLs
- **WALKTHROUGHS.html** - Index of all 49 AI-generated walkthroughs

## Setup Instructions

### 1. Enable GitHub Pages

1. Go to your repository on GitHub
2. Click **Settings** → **Pages**
3. Under "Build and deployment":
   - Source: **GitHub Actions**
4. Save

### 2. Push to GitHub

The GitHub Actions workflow will automatically deploy the `docs/` folder to GitHub Pages on every push to `main`.

```bash
git add .
git commit -m "Add GitHub Pages site"
git push origin main
```

### 3. Access Your Site

After the workflow completes (check Actions tab), your site will be available at:

```
https://yourusername.github.io/zwalker/
```

## Manual Updates

To regenerate the pages locally:

```bash
# Regenerate game sources page
python3 scripts/generate_game_sources_page.py

# Regenerate walkthroughs page
python3 scripts/generate_walkthroughs_page.py
```

## Directory Structure

```
docs/
├── index.html              # Main page
├── GAME_SOURCES.html       # Game index
├── WALKTHROUGHS.html       # Walkthrough index
├── *.md                    # Documentation (Markdown)
├── CHANGELOG.md
├── STATUS.md
├── CZECH_RESULTS.md
└── etc.
```

## Automatic Deployment

The `.github/workflows/pages.yml` workflow:
- Triggers on push to `main`
- Uploads the entire `docs/` directory
- Deploys to GitHub Pages
- Takes ~1-2 minutes

## Linking from README

Add this to your main README.md:

```markdown
## Documentation

📚 **[View Full Documentation & Game Index](https://yourusername.github.io/zwalker/)**

- [100+ Game Sources](https://yourusername.github.io/zwalker/GAME_SOURCES.html)
- [AI-Generated Walkthroughs](https://yourusername.github.io/zwalker/WALKTHROUGHS.html)
- [Test Suite Results](https://yourusername.github.io/zwalker/#testing)
```

## Custom Domain (Optional)

To use a custom domain:

1. Create a `CNAME` file in `docs/`:
   ```
   zwalker.yourdomain.com
   ```

2. Configure DNS:
   - Add CNAME record pointing to `yourusername.github.io`

3. Enable in Settings → Pages → Custom domain

## Maintenance

The pages are static HTML and don't require server-side processing. Update by:

1. Editing HTML files in `docs/`
2. Committing and pushing to GitHub
3. Workflow auto-deploys in ~1 minute

## Features

- Responsive design (mobile-friendly)
- No JavaScript required
- Fast loading (~50KB total)
- Links to JSON walkthroughs
- External links to game sources
- Clean, modern UI
