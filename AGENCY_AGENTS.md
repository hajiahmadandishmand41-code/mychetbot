# Agency Agents integration

MyChatBot vendors the upstream **Agency Agents** project as a Git submodule at `agency-agents/`.

Pinned upstream commit: [`3c9588880b7cafaec325a104899fd8bbe27e7d72`](https://github.com/msitarzewski/agency-agents/commit/3c9588880b7cafaec325a104899fd8bbe27e7d72)

This preserves the upstream source structure and its agent/tooling catalog without copying or rewriting the source. The pinned snapshot contains the Agency roster, divisions, tool definitions, conversion/install scripts, examples, and integration documentation.

## Exact entry points

- [Upstream README](https://github.com/msitarzewski/agency-agents/blob/3c9588880b7cafaec325a104899fd8bbe27e7d72/README.md)
- [Division catalog](https://github.com/msitarzewski/agency-agents/blob/3c9588880b7cafaec325a104899fd8bbe27e7d72/divisions.json)
- [Tool catalog](https://github.com/msitarzewski/agency-agents/blob/3c9588880b7cafaec325a104899fd8bbe27e7d72/tools.json)
- [Conversion engine](https://github.com/msitarzewski/agency-agents/blob/3c9588880b7cafaec325a104899fd8bbe27e7d72/scripts/convert.sh)
- [Installer](https://github.com/msitarzewski/agency-agents/blob/3c9588880b7cafaec325a104899fd8bbe27e7d72/scripts/install.sh)
- [Agent linter](https://github.com/msitarzewski/agency-agents/blob/3c9588880b7cafaec325a104899fd8bbe27e7d72/scripts/lint-agents.sh)

## Using it locally

```bash
git clone --recurse-submodules https://github.com/hajiahmadandishmand41-code/mychetbot.git
cd mychetbot/agency-agents
./scripts/convert.sh
./scripts/install.sh --help
```

The submodule is deliberately isolated from `mychetbot`'s Next.js/Python/Android roots so upstream `.github` workflows do not execute inside the parent repository and the existing application routing/deployment remains untouched.
