import type { ConfigGroup, ControlPlaneData } from '../types';

export function GlobalConfigSection({ data }: { data: ControlPlaneData }) {
  const groups: ConfigGroup[] = data.global_config ?? [];

  return (
    <>
      <div className="cat-head">
        <h1>Codex global config</h1>
        <span className="cat-hint">what every Codex session inherits, rendered to ~/.codex/config.toml</span>
      </div>

      {groups.length === 0 ? (
        <div className="empty-state">
          <p>No global configuration found for Codex.</p>
        </div>
      ) : (
        <div className="gc-grid">
          {groups.map((group) => (
            <section className="gc-card" key={group.title}>
              <header className="gc-card-head">
                <h2>{group.title}</h2>
                <a className="gc-src" href={`/source/${group.source}`} title={group.source}>
                  <code>{group.source}</code>
                </a>
              </header>
              <dl className="gc-rows">
                {group.rows.map((row, i) => (
                  <div className="gc-row" key={`${row.label}-${i}`}>
                    <dt>{row.label}</dt>
                    <dd className={`gc-val${row.tone ? ` gc-${row.tone}` : ''}`}>{row.value}</dd>
                  </div>
                ))}
              </dl>
            </section>
          ))}
        </div>
      )}
    </>
  );
}
