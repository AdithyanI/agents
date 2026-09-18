# Configuration and Credentials

Follow the owning tool's existing configuration contract. Keep shared project policy in tracked config, machine/user preferences in their local home, and invocation-specific choices in flags. Prefer the platform's established locations rather than scattering new dotfiles.

Make precedence explicit. A common order is flags, environment overrides, project config, user config, then system defaults; preserve the order already promised to consumers.

When authorized work changes another program's configuration, update only the owned keys or generated surface and explain the material change. Reuse existing authorization; seek a decision only for an unresolved or out-of-scope effect. Prefer the established canonical renderer over appending competing config.

Use environment variables for non-secret contextual settings. Choose names scoped to the tool and avoid repurposing common variables such as HOME. Respect conventional proxy, temporary-directory, and terminal settings where the underlying tool supports them.

Do not use environment variables or flags as secret-value inputs. Prefer credential files, stdin/pipes, local sockets, or secret managers, and redact success/error/debug output. A credential-file environment override can contain a path. In this environment, the `secret-management` skill owns canonical secret materialization; do not create a parallel credential store.

`.env` is a materialization format where the consumer requires it, not a reason to invent another hand-maintained source of truth. File credentials may need whole-file materialization rather than KEY=value conversion.
