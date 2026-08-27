# Agency Agents integration

MyChatBot vendors the upstream **Agency Agents** project as a Git submodule at `agency-agents/`.

Pinned upstream commit: [`3c9588880b7cafaec325a104899fd8bbe27e7d72`](https://github.com/msitarzewski/agency-agents/commit/3c9588880b7cafaec325a104899fd8bbe27e7d72)

The pinned source contains the Agency roster, division catalog, tool definitions, conversion/install scripts, examples, and integration documentation. It is isolated under `agency-agents/` so the parent Next.js/Python/Android project keeps its own CI and deployment boundaries.

## Exact source links

- [Upstream README](https://github.com/msitarzewski/agency-agents/blob/3c9588880b7cafaec325a104899fd8bbe27e7d72/README.md)
- [Division catalog](https://github.com/msitarzewski/agency-agents/blob/3c9588880b7cafaec325a104899fd8bbe27e7d72/divisions.json)
- [Tool catalog](https://github.com/msitarzewski/agency-agents/blob/3c9588880b7cafaec325a104899fd8bbe27e7d72/tools.json)
- [Convert engine](https://github.com/msitarzewski/agency-agents/blob/3c9588880b7cafaec325a104899fd8bbe27e7d72/scripts/convert.sh)
- [Installer](https://github.com/msitarzewski/agency-agents/blob/3c9588880b7cafaec325a104899fd8bbe27e7d72/scripts/install.sh)
- [Agent linter](https://github.com/msitarzewski/agency-agents/blob/3c9588880b7cafaec325a104899fd8bbe27e7d72/scripts/lint-agents.sh)
- [Agency integrations](https://github.com/msitarzewski/agency-agents/tree/3c9588880b7cafaec325a104899fd8bbe27e7d72/integrations)

## Major divisions

[Academic](https://github.com/msitarzewski/agency-agents/tree/3c9588880b7cafaec325a104899fd8bbe27e7d72/academic) · [Design](https://github.com/msitarzewski/agency-agents/tree/3c9588880b7cafaec325a104899fd8bbe27e7d72/design) · [Engineering](https://github.com/msitarzewski/agency-agents/tree/3c9588880b7cafaec325a104899fd8bbe27e7d72/engineering) · [Finance](https://github.com/msitarzewski/agency-agents/tree/3c9588880b7cafaec325a104899fd8bbe27e7d72/finance) · [Game Development](https://github.com/msitarzewski/agency-agents/tree/3c9588880b7cafaec325a104899fd8bbe27e7d72/game-development) · [GIS](https://github.com/msitarzewski/agency-agents/tree/3c9588880b7cafaec325a104899fd8bbe27e7d72/gis) · [Healthcare](https://github.com/msitarzewski/agency-agents/tree/3c9588880b7cafaec325a104899fd8bbe27e7d72/healthcare) · [Marketing](https://github.com/msitarzewski/agency-agents/tree/3c9588880b7cafaec325a104899fd8bbe27e7d72/marketing) · [Paid Media](https://github.com/msitarzewski/agency-agents/tree/3c9588880b7cafaec325a104899fd8bbe27e7d72/paid-media) · [Product](https://github.com/msitarzewski/agency-agents/tree/3c9588880b7cafaec325a104899fd8bbe27e7d72/product) · [Project Management](https://github.com/msitarzewski/agency-agents/tree/3c9588880b7cafaec325a104899fd8bbe27e7d72/project-management) · [Research](https://github.com/msitarzewski/agency-agents/tree/3c9588880b7cafaec325a104899fd8bbe27e7d72/research) · [Sales](https://github.com/msitarzewski/agency-agents/tree/3c9588880b7cafaec325a104899fd8bbe27e7d72/sales) · [Security](https://github.com/msitarzewski/agency-agents/tree/3c9588880b7cafaec325a104899fd8bbe27e7d72/security) · [Spatial Computing](https://github.com/msitarzewski/agency-agents/tree/3c9588880b7cafaec325a104899fd8bbe27e7d72/spatial-computing) · [Specialized](https://github.com/msitarzewski/agency-agents/tree/3c9588880b7cafaec325a104899fd8bbe27e7d72/specialized) · [Support](https://github.com/msitarzewski/agency-agents/tree/3c9588880b7cafaec325a104899fd8bbe27e7d72/support) · [Testing](https://github.com/msitarzewski/agency-agents/tree/3c9588880b7cafaec325a104899fd8bbe27e7d72/testing)

## Local checkout

```bash
git clone --recurse-submodules https://github.com/hajiahmadandishmand41-code/mychetbot.git
cd mychetbot/agency-agents
./scripts/convert.sh
./scripts/install.sh --help
```
