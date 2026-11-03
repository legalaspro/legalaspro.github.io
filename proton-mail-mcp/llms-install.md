# Installing mcp-proton-mail: a guide for AI agents

Covers the latest version on PyPI (https://pypi.org/project/mcp-proton-mail/). Guide updated 3 November 2026.
Human page: https://manajev.com/proton-mail-mcp/

You are an AI agent installing mcp-proton-mail for a person on their own computer. It is an
unofficial MCP server for Proton Mail Bridge, not affiliated with Proton AG. You run the installer
and read its JSON; the person does the one thing only they can do, the Bridge login, in their own
terminal.

Never ask the person for their Proton password, their Bridge password, a two-factor code or the
bearer token, and never put any of them in a command, a file or a message.

## Check the name

- PyPI package: `mcp-proton-mail` (https://pypi.org/project/mcp-proton-mail/)
- MCP Registry name: `io.github.legalaspro/proton-mail-mcp`
- Source: https://github.com/legalaspro/proton-mail-mcp
- Command: `proton-mail-mcp`, also installed as `mcp-proton-mail`. Server name in client configs:
  `proton-mail`.

It ships only as the PyPI package above and its GitHub source, with no app download or .exe.
Install only that package.

Every command below starts with `uvx mcp-proton-mail`. uvx caches the first version it fetches; use `uvx mcp-proton-mail@latest` to get the newest release.

## 1. What the person needs

- A paid Proton plan, which Proton Mail Bridge requires.
- Linux (Debian/Ubuntu, Fedora/RHEL or Arch) or macOS. On macOS, [Homebrew](https://brew.sh)
  unless Bridge is already installed. On Linux, `secret-tool` (`libsecret-tools` on Debian and
  Ubuntu) with an unlocked keyring, or an initialised `pass` store.
- Native Windows support is new and has run only on Windows Server CI runners: read
  https://github.com/legalaspro/proton-mail-mcp/blob/main/docs/windows.md first, or use WSL2 and
  the Linux steps.
- [uv](https://docs.astral.sh/uv/).

## 2. Plan

```sh
uvx mcp-proton-mail setup --dry-run --json --client <client>
```

`<client>` is one of `claude-desktop`, `claude-code`, `chatgpt`, `codex`, `gemini`, `cursor` or
`grok-bot`, and `--client` is repeatable. Nothing changes. `--json` prints one JSON document on
stdout (progress goes to stderr) and never opens a prompt.

Read `result`, `next` and `needs_user`. Each `needs_user` entry has `id`, `text`, `when`
(`before`, `during` or `after`), `blocking`, `stops_run` (it would stop the same run with
`--yes`), `needs_terminal`, and for those the `command` the person runs. Tell the person what
`needs_user` says they will do.

- `quit_bridge_app`: ask the person to quit the Proton Mail Bridge app and turn off its
  start-at-login setting, or rerun with `--skip-bridge-service` to keep the app running Bridge.
- `store_tools` or `secret_service`: its `text` says what to install or where to run.
- `sudo`: installing Bridge needs the person's sudo password, which only their own terminal may
  take. Hand it over as in step 3.

Field details: https://github.com/legalaspro/proton-mail-mcp/blob/main/docs/install.md#agents-and-scripts

## 3. Hand the login to the person

If `bridge_login`, `bridge_password` or `sudo` is listed, stop and give the person its `command`
exactly as printed, to run in their own terminal. Do not run it yourself, and do not run it
through a pseudo-terminal or a pipe of yours.

Tell them what happens there:

- Setup opens Bridge's own CLI. They type `login`, their Proton email and password (pasting
  works), and the two-factor code if asked.
- If Bridge prints a verification link, they open it in any browser, finish the check, then press
  Enter in the terminal.
- Setup reads the IMAP username from Bridge, then asks for the Bridge password at a hidden prompt.
  That is the password Bridge's `info` just showed, not their Proton password.
- On macOS, Keychain may ask for access: choose Always Allow.
- Setup shows its plan and asks before applying it. Then it installs and starts everything:
  Bridge's package, the server's environment and the per-user services.

Everything they type goes into Bridge's prompts or the installer's hidden prompt, never through
you. Wait until they say it finished.

## 4. Apply and verify

```sh
uvx mcp-proton-mail setup --yes --json --client <client>
```

After the person's run, this finds everything in place, and repeating it is safe. Expect `result`
`done`.

- `needs_user`: go back to step 3 with the entries whose `stops_run` is true.
- `failed` or `refused`: `error` says why and what to do. A client config the installer cannot
  edit safely refuses the whole plan before any step runs.

Report the document's `connector` to the person: the command and arguments any MCP client on this
computer can start, and the server's URL. It holds no token, and you never need one.

## 5. More clients, or only the entry

```sh
uvx mcp-proton-mail configure-client --yes --json --client <client>
uvx mcp-proton-mail configure-client --client <client> --print-config
```

The first adds another client and keeps the old config as a dated backup. The second prints the
exact entry for this computer and changes nothing; ChatGPT's token shows as a placeholder.

| Client | `--client` | Config it writes | Token in the file |
| --- | --- | --- | --- |
| Claude Desktop | `claude-desktop` | `claude_desktop_config.json` | No |
| Claude Code | `claude-code` | `~/.claude.json`, via `claude mcp add --scope user` when on PATH | No |
| ChatGPT Mac app | `chatgpt` | `~/.codex/config.toml`, shared with Codex; direct HTTP | Yes, file is owner-only |
| Codex | `codex` | `~/.codex/config.toml`, via `codex mcp add` when on PATH | No, unless ChatGPT is set up too: Codex then uses ChatGPT's entry |
| Gemini CLI | `gemini` | `~/.gemini/settings.json`, via `gemini mcp add --scope user` when on PATH | No |
| Cursor | `cursor` | `~/.cursor/mcp.json` | No |
| Grok Bot and other local agents | `grok-bot` | None; setup shows the entry to add | No |

Every client but ChatGPT starts `proton-mail-mcp connect` by absolute path, a local stdio relay
that reads the token itself. For Codex and ChatGPT, add `tool_timeout_sec = 150` by hand under
`[mcp_servers.proton-mail]` in `~/.codex/config.toml`. Codex's default tool timeout is 60
seconds, shorter than the server's call budget.

Any other client on the same computer can use MCP Streamable HTTP at `http://127.0.0.1:8765/mcp`
with `Authorization: Bearer <token>`. The person gets the token with
`uvx mcp-proton-mail show-token --copy`, which puts it on their clipboard without showing it. A
client in someone else's cloud cannot reach this address.

## 6. First test

Relay each `needs_user` entry whose `when` is `after`, such as restarting the client. Then suggest
the person pastes this into a new chat:

> Using the proton-mail tools, how many unread messages are in my Inbox? List the five newest with
> sender, subject and date. Don't change anything.

It should call `count_mail` and `search_mail`, which read only and mark nothing read.

## 7. After install

- Apart from saving drafts or attachments and `undo_action`, every change needs a preview, a
  single-use token tied to it, and the person's OK. For mailbox changes and saved rules, the
  client's form asks for that OK. Show the preview to the person and wait for their OK; never
  answer the form for them. Call `undo_action` only when the person asks.
- Sending is off by default. Do not set `PROTON_MCP_ENABLE_SEND=1` unless the person asks for it;
  see [Sending mail](https://github.com/legalaspro/proton-mail-mcp/blob/main/docs/sending.md).
- Mail you read becomes part of your conversation and goes wherever your model runs. Read only
  what the task needs.

## Uninstall

```sh
uvx mcp-proton-mail uninstall --dry-run
uvx mcp-proton-mail uninstall
```

It keeps stored credentials unless `--remove-credentials`, Bridge unless `--remove-bridge`, and
each client's `proton-mail` entry, which the person removes.

## Hosts without systemd

In a container or on a system without systemd, setup starts the MCP server and Bridge as
background processes and runs its self-check. They stop when the host restarts; run setup again
then. See https://github.com/legalaspro/proton-mail-mcp/blob/main/docs/install.md#hosts-without-systemd
