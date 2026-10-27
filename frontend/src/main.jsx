import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Area, AreaChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import './styles.css';

const DEFAULT_DATE = '2026-01-15';
const fmt = new Intl.NumberFormat('en-GB', { maximumFractionDigits: 0 });
const fmtMW = value => value == null ? '—' : `${fmt.format(value)} MW`;

function App() {
  const [date, setDate] = useState(DEFAULT_DATE);
  const [cutoff, setCutoff] = useState('12:00');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function load() {
    setLoading(true); setError('');
    const prior = new Date(`${date}T00:00:00Z`); prior.setUTCDate(prior.getUTCDate() - 1);
    const cutoffIso = `${prior.toISOString().slice(0, 10)}T${cutoff}:00Z`;
    try {
      const res = await fetch(`/api/assessment?deliveryDate=${date}&cutoff=${encodeURIComponent(cutoffIso)}`);
      const body = await res.json();
      if (!res.ok) throw new Error(body.detail || 'Unable to load Elexon data.');
      setData(body);
    } catch (e) { setError(e.message); setData(null); }
    finally { setLoading(false); }
  }
  useEffect(() => { load(); }, []);
  const chart = useMemo(() => (data?.points || []).map(p => ({ ...p, time: new Date(p.startTime).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', timeZone: 'UTC' }) })), [data]);
  const m = data?.metrics;
  return <main>
    <header><div className="brand"><span className="mark">↯</span><div><h1>Wind Procurement Desk</h1><p>Day-ahead wind intelligence · GB national</p></div></div><div className="scope">JANUARY 2026 PILOT</div></header>
    <section className="intro"><div><p className="eyebrow">DECISION SUPPORT</p><h2>Buy with the forecast you actually had.</h2><p>Compare half-hourly wind outturn with the latest forecast available at your day-ahead decision cut-off. Positive error is missing wind versus plan.</p></div><div className="method"><strong>Data boundary</strong><span> Elexon WINDFOR + FUELHH (WIND)</span><strong>Resolution</strong><span> 30-minute settlement periods</span></div></section>
    <section className="controls" aria-label="Decision controls"><label>Delivery date<input type="date" min="2026-01-01" max="2026-01-31" value={date} onChange={e => setDate(e.target.value)} /></label><label>Decision cut-off (UTC)<input type="time" value={cutoff} onChange={e => setCutoff(e.target.value)} /></label><button onClick={load} disabled={loading}>{loading ? 'Refreshing…' : 'Refresh decision view'}</button><p>The selected cut-off applies on D−1. Later updates are excluded.</p></section>
    {error && <section className="error"><strong>Data unavailable.</strong> {error}<br/><small>Check the public Elexon service and retry. No substituted values are shown.</small></section>}
    {data && <><section className="metrics">
      <Metric label="Matched periods" value={`${m.count} / 48`} hint="Forecast and actual available" />
      <Metric label="Mean absolute error" value={fmtMW(m.maeMw)} hint="Typical half-hour error" />
      <Metric label="Bias" value={fmtMW(m.biasMw)} hint={m.biasMw > 0 ? 'Under-forecast on average' : 'Over-forecast on average'} tone={m.biasMw > 0 ? 'risk' : ''} />
      <Metric label="RMSE" value={fmtMW(m.rmseMw)} hint="Penalises larger misses" />
      <Metric label="P90 downside reserve" value={fmtMW(m.p90DownsideMw)} hint="Historical under-forecast proxy" tone="risk" />
    </section>
    <section className="panel"><div className="panel-head"><div><p className="eyebrow">DELIVERY PROFILE</p><h3>Forecast versus wind outturn</h3></div><p className="legend-note">All values MW · UTC</p></div>{chart.length ? <div className="chart"><ResponsiveContainer width="100%" height={340}><AreaChart data={chart} margin={{ top: 15, right: 14, left: 0, bottom: 0 }}><defs><linearGradient id="actual" x1="0" x2="0" y1="0" y2="1"><stop stopColor="#39cfb0" stopOpacity=".45"/><stop offset="1" stopColor="#39cfb0" stopOpacity=".03"/></linearGradient></defs><CartesianGrid stroke="#dce4ea" vertical={false}/><XAxis dataKey="time" interval={5} tick={{fill:'#607083',fontSize:12}}/><YAxis tickFormatter={v => `${v/1000}k`} tick={{fill:'#607083',fontSize:12}}/><Tooltip formatter={(v, n) => [fmtMW(v), n === 'actualMw' ? 'Actual wind' : 'Eligible forecast']} labelFormatter={v => `Settlement period ${v} UTC`}/><Legend formatter={v => v === 'actualMw' ? 'Actual wind' : 'Eligible forecast'} /><Area type="monotone" dataKey="actualMw" stroke="#008c78" strokeWidth={3} fill="url(#actual)"/><Area type="monotone" dataKey="forecastMw" stroke="#285b9e" strokeWidth={2.5} fill="none" strokeDasharray="7 5"/></AreaChart></ResponsiveContainer></div> : <div className="empty">No comparable forecast/actual pairs were returned for this decision view.</div>}</section>
    <section className="explain"><div><p className="eyebrow">HOW TO USE THIS</p><h3>Turn forecast error into procurement awareness.</h3></div><ol><li><b>Set delivery day</b> and the point when the desk made its day-ahead choice.</li><li><b>Read P90 downside reserve</b> as the historical magnitude of wind shortfall exceeded in only 10% of matched periods; it is a planning cue, not a trading instruction.</li><li><b>Inspect the profile</b> to see exactly when the renewable position was most exposed.</li></ol></section>
    </>}
    <footer><span>Source: Elexon Insights API · {data?.source.actuals || 'FUELHH / WIND'} · {data?.source.forecasts || 'WINDFOR'}</span><span>Forecast selection: latest publish time ≤ decision cut-off</span></footer>
  </main>
}
function Metric({label,value,hint,tone}) { return <article className={`metric ${tone || ''}`}><p>{label}</p><strong>{value}</strong><span>{hint}</span></article> }
createRoot(document.getElementById('root')).render(<App />);
