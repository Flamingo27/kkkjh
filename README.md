# Wind Procurement Desk

Decision support for UK day-ahead power purchasing teams. It compares Elexon national wind forecasts with FUELHH wind outturn, selecting only the forecast that would have been available at the chosen day-ahead decision cut-off.

**Live application:** https://1-problem-setting-consider-that-23xpxtbti.vercel.app

## Repository layout

```
.
├── backend/
│   ├── app/
│   │   ├── main.py       # FastAPI routes and production static-file serving
│   │   ├── elexon.py     # Elexon data retrieval and date-window handling
│   │   └── logic.py      # As-of forecast selection and error calculations
│   ├── tests/            # Unit tests for the core decision logic
│   └── requirements.txt  # Python runtime dependencies
├── frontend/
│   ├── src/              # React dashboard and styles
│   ├── index.html        # Frontend entry document
│   ├── package.json      # JavaScript dependencies and commands
│   └── vite.config.js    # Development server and API proxy configuration
├── Dockerfile             # Single-container production build
├── docker-compose.yml     # Local Docker launcher
├── vercel.json            # Vercel deployment configuration
└── README.md              # Product, operational, and technical documentation
```

## What it does

- Shows the latest **eligible** wind forecast for a selected delivery day and decision time.
- Overlays the selected forecast and actual wind generation in MW, in 30-minute settlement periods.
- Quantifies bias, MAE, RMSE, signed error and a P90 downside-error reserve proxy.
- Keeps the data scope deliberately narrow: Elexon `WINDFOR` and `FUELHH` records where `fuelType=WIND`.

## Day-ahead logic

For every delivery half-hour, the backend chooses the forecast with the greatest `publishTime` that is no later than the decision cut-off. This avoids look-ahead bias: a forecast published after the purchasing decision cannot influence its assessment. The default cut-off is 12:00 UTC on the preceding day, which is editable in the UI to match the client’s trading process.

`error_mw = actual_mw - forecast_mw`; a positive error means wind was under-forecast, creating an incremental procurement risk.

## Run locally

```bash
docker compose up --build
```

Open http://localhost:8080. The API is served under `/api` by the same container in production. For development, start the backend and frontend separately with the commands in `backend/requirements.txt` and `frontend/package.json`.

```bash
# terminal 1
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000

# terminal 2
cd frontend
npm install && npm run dev
```

### Data access

The service calls the public Elexon Insights API at `https://data.elexon.co.uk/bmrs/api/v1`. It requests January 2026 records only when that month is selected and filters actuals to `fuelType=WIND`. Elexon raw datasets are publication-time filtered, so the service requests the two days ending at the decision cut-off, then selects the eligible revision per target period. API response shapes are validated defensively; a clear, recoverable error is shown if Elexon is unavailable.

### Tests

```bash
cd backend
python -m pytest
```

## Deployment

The repository includes `vercel.json` for an API deployment and a static frontend build. Set `ELEXON_BASE_URL` only if the client uses an approved Elexon proxy. A deployment needs the client’s Vercel account/token and project linkage, which are not present in this workspace, so it has not been published from here. For a single-container host, use the supplied `Dockerfile` and expose port 8080.

## Client pitch

**Wind Procurement Desk turns a sprawling sequence of weather-driven updates into an auditable day-ahead decision view.** At the instant your traders need to commit, it shows the latest forecast they could actually have seen, the half-hourly MW exposure, and the historical error distribution behind a prudent reserve. It is deliberately focused: one national wind signal, one trusted public source, transparent calculation rules. That makes it quick to adopt now and a clean foundation for future demand, price, and portfolio inputs.

## Technical review notes

The React single-page client owns interaction and charting; the FastAPI service owns Elexon retrieval, decision-time selection, joins, and metrics. This separation keeps market logic server-side and testable. The data adapter isolates upstream query/shape changes. `select_as_of` is a pure function with unit tests for the important no-look-ahead invariant. No database is needed for this first version: January requests are bounded, while production scaling can add an immutable raw-data cache plus scheduled ingestion without changing the API contract.

## AI assistance

AI tools were used to accelerate initial implementation, documentation, and test scaffolding. The forecast-selection rule, data constraints, and final code should still be reviewed by the client’s trading and engineering owners before production use.

## Important scope note

This is decision support, not an automated trading system. It does not calculate total procurement because the requested scope excludes demand, price, outages, and other generation inputs.
