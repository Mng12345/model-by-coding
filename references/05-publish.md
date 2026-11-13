# 05 — Publishing

Three artefacts get published, and they have different rules: the **skill
repository** (source only), the **video** (a Release asset, and optionally
YouTube/X), and the **community-list entry** (a small PR pointing at the repo).

## 1. What belongs in git, and what does not

In git:

- `SKILL.md`, `references/`, `scripts/` — the skill itself;
- `examples/<object>/` — source, photos, build scripts, blueprint/measurement
  notes, and any small diagnostics;
- `README.md`, `LICENSE`, `.gitignore`.

Not in git:

- rendered video and audio masters — the example's film is 37,652,626 bytes and
  its `mix.wav` is 43.5 s of 48 kHz stereo; both live on a GitHub Release
  instead of in the history;
- `node_modules/`, `dist/` bundles, `.hyperframes/artifacts/`, snapshots and
  render output.

A `.gitignore` that matches the pipeline:

```gitignore
node_modules/
dist/
video/renders/
video/.hyperframes/
video/assets/vendor/*.min.js
out/
```

Adjust the vendored-file line if the repository is meant to be runnable without
a build step; a vendored minified bundle is legitimate to commit when it is the
only way to reproduce the example.

Commit message for the first public state should say what the example proves,
not "initial commit": `Fan teardown example: 13 parts, 43.5 s HyperFrames film`.

## 2. GitHub Release

Releases keep binaries out of git history while still serving them from the
repository page. `gh` is installed on this machine (2.103.3) and
`gh release create` does exactly this:

```powershell
git tag -a v1.0.0 -m "model-by-coding v1.0.0"
git push origin v1.0.0

gh release create v1.0.0 `
  "renders/video_<date>.mp4#Teardown film, 1920x1080 30fps" `
  "assets/audio/mix.wav#Soundtrack mix" `
  --title "v1.0.0 — model-by-coding" `
  --notes "Build a 3D model from photos, render a teardown film with HyperFrames, verify it against the photos, cut a GIF."
```

Behaviour verified in `gh release create --help`:

- asset files are positional arguments; append `#visible label` after a path to
  give the asset a display name;
- when assets are attached, gh creates a draft release, uploads the assets, and
  publishes only after all uploads finish — an interrupted run leaves a draft
  you can retry rather than a half-broken release;
- `--verify-tag` aborts if the tag does not already exist (useful in CI);
- `--generate-notes` builds release notes from the API, `--draft` leaves the
  release unpublished.

Verify the result instead of assuming: `gh release view v1.0.0` lists the assets
and their sizes. Open the page once and download the film; a Release that only
exists in the CLI output is not published.

Pitfalls: pushing the tag before the release (fine, but then `--verify-tag` is
required to fail-fast on typos); uploading a file larger than the repository's
release-asset limit (check GitHub's current limits; a 40 MB film is far below
any of them); and forgetting that Release assets are immutable on some
repositories once published — fix by uploading a new asset, not by editing.

## 3. The skill repository

What a good skill repository contains:

- `SKILL.md` — YAML frontmatter with `name` (matches the folder name) and a
  one-sentence English `description` that starts with when to use it; body under
  ~300 lines; routing table to `references/`; one minimal runnable command
  sequence.
- `references/` — the depth: methods, parameters, criteria, failure modes. A
  reader should be able to reproduce the example without opening the example.
- `scripts/` — parameterised helpers that run as-is: no hard-coded object name,
  no absolute path, `--help` works.
- `examples/` — at least one complete object with photos and the measurement
  notes that justify its dimensions.
- `README.md` — what it is, quickstart, structure, requirements, example output.
- `LICENSE` — pick one before publishing; the example repository uses MIT.

Requirements to state in the README (versions verified on this machine):
Node 22.19.0, Python 3.11.1 with Pillow, ffmpeg, Chrome (157.0.8103.40 here) for
headless screenshots, and HyperFrames 0.9.36 pinned via `npx --yes
hyperframes@0.9.36`. Say "minimum tested" rather than hard requirements where
the tool is version-agnostic.

Installation is client-specific: copy or symlink the folder into the directory
the agent loads skills from, reload the agent, and confirm the skill appears in
its skill list. Do not document a path you have not tested on the target client;
"the skills directory used by your agent" is honest.

Quality gate before publishing: run every command in `SKILL.md` and each
reference from a clean shell in a fresh clone; run `python -m py_compile
scripts/*.py`; open each `scripts/*.py --help`; and make sure no script mentions
the example object by name. A skill that only works in the author's checkout is
not a skill.

## 4. Community skill-list PR

Lists that index Agent Skills usually accept one entry: the repository (or the
skill folder) plus a one-line description. The rules are set by each list, so
read its `CONTRIBUTING.md`/`README.md` before touching anything.

Procedure:

1. Find the list's entry format and ordering rule (alphabetical, category
   sections, machine-generated index).
2. Fork, branch (`add-model-by-coding`), add exactly one entry in the right
   place, matching the surrounding format (including trailing punctuation).
3. If the list generates its index with a script, run that script; do not
   hand-edit generated files.
4. Open one PR that touches one section, with the description copied from the
   skill's frontmatter, and state that the skill is runnable end-to-end.
5. Respond to review; keep the PR rebased; do not mix unrelated fixes.

Pitfalls: entries whose link 404s after a rename (point at the repository root,
not a deep path); descriptions that advertise instead of describing ("the
ultimate...") — lists usually reject them; adding a second entry for a
sub-skill; claims that require credentials; and expecting speed — many lists
are maintained by one person. Some lists require the skill to include its
license in the folder and to avoid platform-specific absolute paths; both are
already true if §3 was followed.

## 5. YouTube

Upload the `--quality delivery` MP4: 1920×1080, 30 fps, H.264 + AAC in the
example, which is exactly what YouTube expects, so no re-encoding decisions are
needed.

- Upload as unlisted first, watch the 43.5 s once end to end, then publish.
- Thumbnail: grab a frame from the exploded hold via `snapshot --at`; a still
  with all parts separated reads better as a thumbnail than the front view.
- Description: what was modelled, that it is code (Three.js) rendered with
  HyperFrames, and a link to the repository with the skill and the source.
- Chapters pay off only if the film is long; a single teardown loop is not.

Two pitfalls worth more than the upload settings:

- **Content ID.** Any music can be claimed even when it is "free". The example's
  first bed was a Pixabay track marked "Content ID Registered": the licence allows
  commercial use, but a YouTube claim was still possible, so the mix was rebuilt
  around a track whose page shows no mark, and the foley is synthesised locally.
  Generating everything you can removes the question; if you use a track, check its
  page for the mark (it follows the uploader) and keep the licence note in the repo.
- **Limits change.** Unverified channels have lower upload limits, and the
  numbers move; check YouTube Studio's current limit for the channel instead of
  trusting a number from a tutorial.

## 6. X and other short-video posts

For this pipeline the natural post is the **GIF from `04-gif.md`**, 3–4 s,
looping, attached with a sentence about what it is and a link to the repo. GIFs
autoplay and loop, which a 43.5 s MP4 does not.

- Add alt text: "White desk fan, 13-part teardown, each part floating apart,
  code-built 3D model rendered as a looping video."
- Crop for the platform: 16:9 for a wide post, 1:1 for a square embed; do not
  letterbox.
- Post the same clip once. Broadcasting it into many communities in one go is
  spam under most platform rules; share it where the topic fits.
- Size and duration limits vary by account and change; check the composer's
  current limit rather than a remembered number.

## 7. Release checklist

- [ ] `check` report `ok: true`, no errors; warnings read and understood
- [ ] `render --quality delivery` finished, duration matches `data-duration`
- [ ] GIF loops cleanly and is under ~1 MB
- [ ] every command in `SKILL.md` re-run from a clean shell
- [ ] `python -m py_compile scripts/*.py` and each `--help` works
- [ ] no absolute paths or object names hard-coded in `scripts/`
- [ ] LICENSE present; photos and any third-party audio have clear provenance
- [ ] tag pushed, `gh release view` lists the film and the mix
- [ ] community-list entry (optional) points at the repository root
- [ ] social post uses the GIF, with alt text and a repo link
