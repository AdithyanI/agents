import { useEffect, useMemo, useState } from 'react';
import { useNavigateRepo } from '../primitives';
import { repoDisplayName, sourceHref } from '../selectors';
import type { ControlPlaneData, Item } from '../types';

function endpoint(item: Item): string {
  if (item.details.url) return String(item.details.url);
  if (item.details.command) return String(item.details.command);
  return 'No endpoint configured';
}

export function McpExplorer({
  data,
  focusName,
}: {
  data: ControlPlaneData;
  focusName?: string;
}) {
  const navigateRepo = useNavigateRepo();
  const items = useMemo(
    () => data.groups.mcp.slice().sort((a, b) => a.name.localeCompare(b.name)),
    [data.groups.mcp],
  );
  const repos = useMemo(
    () => data.groups.repos.slice().sort((a, b) => a.name.localeCompare(b.name)),
    [data.groups.repos],
  );
  const [selectedName, setSelectedName] = useState(focusName ?? '');

  useEffect(() => {
    if (focusName) setSelectedName(focusName);
  }, [focusName]);

  const selected = items.find((item) => item.name === selectedName);
  const visibleItems = selected ? [selected] : items;
  const coveredRepoCount = repos.filter((repo) =>
    visibleItems.some((item) => item.repos.includes(repo.name)),
  ).length;

  return (
    <div className="mcp-view">
      <header className="mcp-head">
        <div>
          <h1>MCP repository coverage</h1>
          <p>Servers configured for Codex in each managed repository.</p>
        </div>
        <dl className="mcp-summary" aria-label="MCP coverage summary">
          <div>
            <dt>Servers</dt>
            <dd>{items.length}</dd>
          </div>
          <div>
            <dt>Repositories</dt>
            <dd>{repos.length}</dd>
          </div>
          <div>
            <dt>Covered repos</dt>
            <dd>{coveredRepoCount}</dd>
          </div>
        </dl>
      </header>

      <nav className="mcp-filters" aria-label="Filter coverage by MCP server">
        <button
          type="button"
          className={!selected ? 'active' : undefined}
          aria-pressed={!selected}
          onClick={() => setSelectedName('')}
        >
          All servers <strong>{items.length}</strong>
        </button>
        {items.map((item) => (
          <button
            key={item.id}
            type="button"
            className={selected?.name === item.name ? 'active' : undefined}
            aria-pressed={selected?.name === item.name}
            onClick={() => setSelectedName(selected?.name === item.name ? '' : item.name)}
          >
            {item.name}
            <strong>{item.repos.length}</strong>
          </button>
        ))}
      </nav>

      <div className="mcp-definition" aria-live="polite">
        {selected ? (
          <>
            <div className="mcp-definition-main">
              <strong>{selected.name}</strong>
              <code>{endpoint(selected)}</code>
            </div>
            <div className="mcp-definition-meta">
              <span>
                {selected.scope === 'global' ? 'All managed repos' : selected.repos.length ? 'Selected repos' : 'Unassigned'}
              </span>
              <span>{selected.repos.length} repos</span>
              <a href={sourceHref(selected)} target="_blank" rel="noreferrer">
                Registry
              </a>
            </div>
          </>
        ) : (
          <p>Select a server to isolate its coverage and inspect its endpoint.</p>
        )}
      </div>

      <div className="mcp-coverage-scroll">
        <table className="mcp-coverage">
          <caption className="visually-hidden">
            MCP servers configured for Codex in each managed repository
          </caption>
          <thead>
            <tr>
              <th scope="col">Repository</th>
              <th scope="col">
                <span>MCP servers</span>
                <code>.codex/config.toml</code>
              </th>
            </tr>
          </thead>
          <tbody>
            {repos.map((repo) => {
              const repoItems = visibleItems.filter((item) => item.repos.includes(repo.name));
              return (
                <tr key={repo.id}>
                  <th scope="row">
                    <button type="button" onClick={() => navigateRepo(repo.name)}>
                      {repoDisplayName(repo.name)}
                    </button>
                  </th>
                  <td className={repoItems.length ? 'has-target' : undefined}>
                    {repoItems.length ? (
                      <div className="mcp-cell-items">
                        {repoItems.map((item) => (
                          <button
                            key={item.id}
                            type="button"
                            className={selected?.name === item.name ? 'active' : undefined}
                            onClick={() => setSelectedName(item.name)}
                          >
                            {item.name}
                          </button>
                        ))}
                      </div>
                    ) : (
                      <span className="mcp-cell-empty" aria-label="No MCP servers">
                        —
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
