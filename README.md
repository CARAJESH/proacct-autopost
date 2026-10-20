# Proacct India – Instagram auto-poster

Posts one finance/accounting carousel to Instagram every evening (about 6:50 pm IST), fully automatically, using Instagram's official API. It runs free on GitHub, so your computer can stay off.

- `posts.json` – 30 ready posts (slide text, caption, hashtags)
- `images/day01 … day30` – the finished 1080×1080 slides
- `post.py` – publishes the next post
- `.github/workflows/daily-post.yml` – the daily schedule
- `render.py` + `fonts/` – rebuild the slides after editing `posts.json`
- `state.json` – which day is next (updated automatically)

---

## One-time setup (about 30 minutes)

### 1. Switch Instagram to a Professional account
Instagram app → Settings → **Account type and tools** → **Switch to professional account** → choose **Creator** or **Business**. Free.

### 2. Put this folder on GitHub
1. Create a free account at github.com.
2. Click **New repository**, name it `proacct-autopost`, choose **Public** (Instagram must be able to download the images), and create it.
3. Upload every file and folder from this zip, including the hidden `.github` folder. The easiest way is **GitHub Desktop** (desktop.github.com): clone the new repo, copy all files into it, then **Commit** and **Push**.
   *Using the website instead?* Upload in batches (100 files at a time), and create the workflow by hand with **Add file → Create new file**, name `.github/workflows/daily-post.yml`, pasting the file's contents.

### 3. Get your Instagram access token
1. Go to developers.facebook.com and log in → **My Apps** → **Create app**.
2. Choose the use case for managing content on Instagram, and finish creating the app.
3. Open **API setup with Instagram login** → **Generate access tokens** → **Add account** and sign in with your Instagram account. Make sure the permissions include `instagram_business_basic` and `instagram_business_content_publish`.
4. Copy the token it shows. Treat it like a password: don't post it or send it to anyone.

### 4. Save the token in GitHub
In your repo: **Settings → Secrets and variables → Actions → New repository secret**
- Name `IG_ACCESS_TOKEN`, value = the token.

Optional but recommended – keeps the token working forever:
- Create a fine-grained token at github.com/settings/tokens with access to this repo and **Secrets: Read and write**.
- Save it as a secret named `GH_PAT`.

The token lasts 60 days and the script renews it every day. With `GH_PAT` set, a renewed token is saved automatically.

### 5. Test, then go live
1. Open the **Actions** tab and enable workflows if asked.
2. Click **Daily Instagram post → Run workflow** with **Dry run** ticked. The log shows the post it would publish.
3. Run it again with **Dry run** unticked. Day 1 is posted to Instagram right away.

From now on it posts the next day's carousel every evening, by itself.

---

## Everyday use
- **Check it worked:** Actions tab (green tick), or `state.json` lists every published post with its link. GitHub emails you if a run fails.
- **Change the time:** edit the `cron` line in the workflow. It's in UTC; IST is UTC + 5:30.
- **Edit a post:** change `posts.json`, run `pip install pillow` then `python render.py`, and push.
- **After day 30:** the run stops with a message. Ask Claude for 30 more posts, add them to `posts.json` with ids 31–60, run `render.py`, push.
- **Pause:** Actions → Daily Instagram post → **⋯ → Disable workflow**.

## Notes
- Content is educational. Re-check any tax rule before reposting it in a later year.
- Instagram allows up to 100 API posts a day, far above this schedule.
