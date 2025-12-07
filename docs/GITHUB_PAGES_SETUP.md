# GitHub Pages Setup Guide

Follow these steps to publish the ZWalker website to GitHub Pages.

## Prerequisites

- GitHub account
- Repository pushed to GitHub

## Step 1: Create GitHub Repository (if not done)

```bash
# On GitHub, create a new repository named "zwalker"
# Then add it as remote:
git remote add origin https://github.com/YOURUSERNAME/zwalker.git

# Push your code
git push -u origin main
```

## Step 2: Enable GitHub Pages

1. Go to your repository on GitHub: `https://github.com/YOURUSERNAME/zwalker`
2. Click **Settings** (top right)
3. In the left sidebar, click **Pages**
4. Under "Build and deployment":
   - **Source**: Select **GitHub Actions**
5. Click **Save**

That's it! The workflow is already configured.

## Step 3: Trigger Deployment

The site will auto-deploy when you push to `main`. To trigger it now:

```bash
git push origin main
```

Or manually trigger:
1. Go to **Actions** tab
2. Click "Deploy GitHub Pages"
3. Click "Run workflow"

## Step 4: Wait for Deployment

1. Go to the **Actions** tab in your repository
2. Watch the "Deploy GitHub Pages" workflow
3. Takes ~1-2 minutes to complete
4. Green checkmark = success

## Step 5: Access Your Site

Your site will be live at:

```
https://YOURUSERNAME.github.io/zwalker/
```

## Step 6: Update Links in README

Edit `README.md` and replace `yourusername` with your actual GitHub username:

```markdown
**[→ View Full Documentation & Game Index](https://YOURUSERNAME.github.io/zwalker/)**

- [100+ Game Sources with Download URLs](https://YOURUSERNAME.github.io/zwalker/GAME_SOURCES.html)
- [49 AI-Generated Walkthroughs](https://YOURUSERNAME.github.io/zwalker/WALKTHROUGHS.html)
- [Complete Test Suite Results](https://YOURUSERNAME.github.io/zwalker/#testing)
```

Then commit and push:

```bash
git add README.md docs/index.html
git commit -m "Update GitHub Pages links with correct username"
git push origin main
```

Also update `docs/index.html` in the footer and download links.

## Troubleshooting

### Pages Not Deploying

**Check Settings → Pages:**
- Source should be "GitHub Actions" (not "Deploy from a branch")

**Check Actions Tab:**
- Look for errors in the workflow run
- Ensure workflow file exists at `.github/workflows/pages.yml`

**Check Permissions:**
- Settings → Actions → General → Workflow permissions
- Should be "Read and write permissions"

### 404 Error

- Wait a few minutes after first deployment
- Clear browser cache
- Check that files exist in `docs/` directory

### Workflow Fails

**Common issues:**
- Repository settings don't allow Actions
- Pages feature not enabled
- Incorrect workflow syntax

**Fix:**
1. Settings → Actions → Allow all actions
2. Settings → Pages → Source: GitHub Actions
3. Re-run workflow

## Custom Domain (Optional)

To use your own domain:

1. **Create CNAME file:**
   ```bash
   echo "zwalker.yourdomain.com" > docs/CNAME
   git add docs/CNAME
   git commit -m "Add custom domain"
   git push
   ```

2. **Configure DNS:**
   - Add CNAME record in your DNS provider
   - Point to: `YOURUSERNAME.github.io`

3. **Enable in GitHub:**
   - Settings → Pages → Custom domain
   - Enter: `zwalker.yourdomain.com`
   - Wait for DNS check (can take 24 hours)

## File Structure

Your published site includes:

```
https://YOURUSERNAME.github.io/zwalker/
├── index.html              # Main page
├── GAME_SOURCES.html       # 100+ games with URLs
├── WALKTHROUGHS.html       # 49 walkthroughs
├── *.md                    # Markdown docs (accessible as raw)
├── games/
│   └── results/
│       └── *_walkthrough.json    # Walkthrough JSONs
└── solutions/
    └── *_solution.json           # AI solution JSONs
```

## Updating the Site

Every push to `main` automatically rebuilds and deploys:

```bash
# Edit HTML files
vim docs/index.html

# Commit and push
git add docs/
git commit -m "Update website content"
git push origin main

# Site updates in ~1-2 minutes
```

## Analytics (Optional)

To add Google Analytics:

1. Get your GA tracking ID
2. Add to `docs/index.html` before `</head>`:
   ```html
   <!-- Google Analytics -->
   <script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
   <script>
     window.dataLayer = window.dataLayer || [];
     function gtag(){dataLayer.push(arguments);}
     gtag('js', new Date());
     gtag('config', 'G-XXXXXXXXXX');
   </script>
   ```

## What Gets Published

The entire `docs/` directory is published, including:
- HTML pages (`.html`)
- Markdown files (`.md`) - accessible as raw text
- JSON walkthroughs in `games/results/` and `solutions/`
- Images, CSS (if added later)

**Note:** The `.md` files are served as plain text (not rendered as HTML) unless you use Jekyll.

## Success Checklist

- [ ] Repository pushed to GitHub
- [ ] Pages enabled in Settings → Pages → Source: GitHub Actions
- [ ] Workflow runs successfully (check Actions tab)
- [ ] Site accessible at `https://YOURUSERNAME.github.io/zwalker/`
- [ ] Links in README updated with correct username
- [ ] Game sources page loads
- [ ] Walkthroughs page loads
- [ ] JSON files accessible

## Next Steps

After setup:
1. Share your site URL in the README
2. Add site URL to repository description
3. Consider adding a custom domain
4. Add more games and walkthroughs
5. Site auto-updates on every push!

---

**Need help?** Check GitHub Pages documentation: https://docs.github.com/en/pages
