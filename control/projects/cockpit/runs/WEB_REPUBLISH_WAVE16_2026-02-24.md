# Web Republish Receipt - Wave16

- Date (UTC): 2026-02-24T10:02:29Z
- Project: cockpit-v2-launch
- Vercel project id: prj_VDbvmiNCVLHMr1xwKUTI5eMCuvx9
- Target: production

## Scope delivered
- Rebuilt source under `/Users/oliviercloutier/Desktop/Cockpit/site/`:
  - `index.html`
  - `styles.css`
  - `app.js`
  - `assets/cockpit-grid.svg`
  - `.vercelignore`
- Editorial blocks included:
  - why V1 failed
  - why V2 works (1:1 fix map)
  - runtime add-ons and product add-ons
  - architecture + memory + dispatch diagrams
  - Wave16 status and launch path
  - FAQ
- Visuals included:
  - 3 diagrams (hierarchy, memory pipeline, dispatch flow)
  - 2 charts (wave timeline, before/now operating quality)

## Deploy command
```bash
cd /Users/oliviercloutier/Desktop/Cockpit/site
vercel deploy --prod -y
```

## Deploy result
- Deployment id: `dpl_DmVaJTGMynGrft2C5ZJcR9GM4nD9`
- Build status: `Ready`
- Inspect URL: `https://vercel.com/pipipopocolis-projects/cockpit-v2-launch/DmVaJTGMynGrft2C5ZJcR9GM4nD9`
- Production deployment URL: `https://cockpit-v2-launch-63jp3ku6l-pipipopocolis-projects.vercel.app`
- Alias URL: `https://cockpit-v2-launch.vercel.app`

## Verification checks
1. `vercel inspect cockpit-v2-launch.vercel.app` -> Ready, created on 2026-02-24.
2. `curl -L https://cockpit-v2-launch.vercel.app` -> returns `Cockpit V2 - Public Explainer` markup.
3. Top-nav anchors present: V1, V2, Add-ons, Architecture, Charts, Wave16, Start, FAQ.

## Notes
- Deployment was direct-to-production per operator request.
- Existing Vercel linkage in `site/.vercel/project.json` was preserved.
