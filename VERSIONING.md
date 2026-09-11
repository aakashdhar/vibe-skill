# Versioning

This repository is versioned with [Semantic Versioning 2.0.0](https://semver.org/)
and released through **git tags**, which GitHub reads natively to create Releases.

## The three moving parts

| Part | File / mechanism | Role |
|---|---|---|
| Current version | [`VERSION`](VERSION) | Single source of truth — one line, `MAJOR.MINOR.PATCH`, no `v` prefix. |
| History | [`CHANGELOG.md`](CHANGELOG.md) | Human-readable record; the entry for the next version is written before tagging. |
| Release marker | annotated git tag `vX.Y.Z` | The thing GitHub picks up and turns into a Release. Tags carry the `v` prefix. |

`VERSION` and the tag always agree: `VERSION` holds `2.0.0`, the tag is `v2.0.0`.

## What each bump means (a prompt framework, not a library)

- **MAJOR** — breaking change to how skills behave or to generated artifacts: renamed or
  restructured owned files, changed model IDs baked into generated output, removed or
  renamed a skill trigger, changed the artifact contract downstream skills parse.
- **MINOR** — backward-compatible additions: a new skill, a new mode or trigger, added
  reference material, enforced wiring that was previously only advisory.
- **PATCH** — fixes with no contract change: correctness bugs, template typos, stale pins,
  doc corrections.

## Cutting a release

1. Land all work on `main`; working tree clean and pushed.
2. Update [`VERSION`](VERSION) to the new number.
3. Add a dated section to [`CHANGELOG.md`](CHANGELOG.md) (Added / Changed / Fixed /
   Removed) and update the compare links at the bottom.
4. Commit: `git commit -m "release: vX.Y.Z"`.
5. Tag annotated: `git tag -a vX.Y.Z -m "vX.Y.Z — <one-line summary>"`.
6. Push both: `git push origin main --follow-tags`.
7. GitHub shows the tag under **Releases / Tags**. Optionally publish release notes from
   the matching `CHANGELOG.md` section.

## Notes

- Pre-releases use a suffix GitHub flags as pre-release: `v2.1.0-rc.1`.
- Never move a published tag. To correct a release, cut the next patch version.
