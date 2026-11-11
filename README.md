# Live Match Dashboard

Private Streamlit hosting trial, prepared 11 November 2026 from your desktop Live Match Dashboard. The desktop version is unchanged.

## Upload and deploy

1. Create a **private** GitHub repository named `Live-Match-Dashboard` (GitHub uses hyphens instead of spaces).
2. Extract the supplied ZIP. Upload the **contents** of `Live Match Dashboard` to the repository root. `app.py` and `requirements.txt` should be at the top level. Include the hidden `.streamlit` folder and the supplied `live_store/Excel Files/formation_dict.xlsx`.
3. Sign into https://share.streamlit.io with your GitHub account and grant access to this private repository.
4. Create an app from that repository, select branch `main`, set the entrypoint to `app.py`, and choose **Python 3.12** in Advanced settings. Deploy.
5. In app settings → Sharing → Who can view this app, select **Only specific people can view this app**. Keep repository access limited to your own account and do not invite other viewers. The privacy is supplied by Streamlit hosting; this code does not contain a separate login screen.
6. Open the app in a signed-out/private browser window and confirm that authentication is required before any dashboard data appears.
7. In the sidebar, expand **Test hosted feed connections**. Enter IDs from a current fixture if the supplied example IDs are unavailable, then click **Test both feeds**. Each provider reports success or its error separately.
8. Select a league and match, then use **Refresh Live Data**. Confirm the score, lineups, charts and a player detail view.

Streamlit currently permits one private Community Cloud app at a time. If you already use that slot, another hosting option is needed; do not make this dashboard public just to deploy it.

Privacy instructions: https://docs.streamlit.io/deploy/streamlit-community-cloud/share-your-app
Deployment instructions: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy

## Repository contents

| Files | Purpose |
| --- | --- |
| `app.py` and the other `.py` modules | Dashboard, calculations, charts, lineups, portraits and feed requests |
| `requirements.txt` | Python packages installed by the host |
| `.streamlit/config.toml` | Theme and server configuration |
| `assets/` and `lineup_positions.json` | Branding, player names, competition labels, portrait ID mapping and pitch positions |
| `reference_data/Scoresway Schedules/*.csv` | The 60 saved Opta fixture lists (2026 / 2627 only) |
| `reference_data/Fotmob Schedules/*.csv` | The 37 saved FotMob fixture lists (2026 / 2627 only) |
| `reference_data/Excel Files/` | Opta event/qualifier dictionaries, formations, league metadata and team badge lookup |
| `live_store/Excel Files/formation_dict.xlsx` | Formation lookup used by existing lineup calculations |
| `.gitignore` | Excludes generated snapshots, photo caches, environments and secrets |

No historical match archive, large player comparison workbook, Anaconda environment, desktop launcher or notebook installation is required. Notebook processing is already bundled as Python. Portrait lookup uses a bundled Reep ID crosswalk (CC0; https://github.com/withqwerty/reep); images remain with their providers.

## Live feeds and storage

FotMob and Scoresway/Opta are called by the hosted Python server, not your browser. No Chrome, Selenium, cookies or interactive verification bypass is used. A successful laptop request does not prove that a cloud IP address will be accepted. HTTP rejection, verification challenges, endpoint changes and unavailable coverage can prevent live data loading. The hosted trial is the decisive connection test.

In competitions with xG coverage, both feeds must succeed for a fresh snapshot. If one fails, the app keeps a previous successful snapshot where one exists and shows its fetch time. A first load with no snapshot shows the error. Competitions marked no xG use Opta alone. The app does not silently replace unavailable FotMob xG with another measure.

Refresh is manual. Snapshots are generated under `live_store/`, with the two latest generations retained per fixture. They are temporary: hosting restarts/redeploys may erase them, and closing a browser tab does not clean the server. They are not written back to GitHub. Photo downloads use `.headshot-cache/`.

The schedules are the saved lists copied on 11 November 2026, not live schedule feeds. **Refresh Schedule Lists** rereads bundled CSVs; it does not download new fixtures. To update, replace the corresponding files under `reference_data/` in GitHub. Update `league_dict.xlsx` when competition coverage changes. Local published season PAR logs are not included; the existing calculated match score/fallback behavior is used.

## Validation completed

Both provider endpoints returned valid match JSON from the local machine. A stored fixture was reprocessed into 2,163 events and 45 player records, and Streamlit AppTest rendered the dashboard without exceptions. Remote portraits and badges were stubbed for that render check. Python package versions are pinned to the test environment. A separate headless server started, but this environment could not reach its localhost agent endpoint; the hosted server, images and access restrictions still need the deployment checks above.

## Run locally

```sh
python -m venv .venv
# Activate the virtual environment, then:
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The access restriction described above applies to Community Cloud. Running this code on another publicly reachable host requires authentication configured on that host.
