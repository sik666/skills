---
name: drawio-mcp-diagram
description: "Create or edit clear, presentation-ready Draw.io architecture and flow diagrams through the official Draw.io MCP server, including editable .drawio output and layout validation."
---

# Draw.io MCP 制图

Use this skill when the user asks to create, redraw, refine, or save a technical diagram in Draw.io, especially when an existing image is supplied as a visual reference. The result should be an editable `.drawio` file, not only a screenshot or a long text prompt.

## Workflow

1. Determine the diagram's purpose, audience, output path, and required visual style. Treat a supplied reference image as a layout/style reference, not as permission to copy unclear or technically incorrect connections.
2. Model the content before drawing it: identify the main actors or areas, the data/control flow, the important branches, and the ownership/lifecycle relationships. Keep only the concepts needed to explain the requested module.
3. Build native Draw.io XML with `mxfile`, `diagram`, `mxGraphModel`, `mxCell`, and `mxGeometry`. Prefer large labeled regions, simple rounded rectangles, orthogonal connectors, and a small consistent color palette. Keep the source readable and save it at the user's requested path.
4. Use the official Draw.io MCP `open_drawio_xml` tool to open the XML in diagrams.net. If the MCP tool is not exposed directly, use the locally installed `@drawio/mcp` server or `npx @drawio/mcp` through a standard MCP client. The MCP input must be the XML string, not a JSON object nested inside the `content` field.
5. Inspect the opened layout and revise the XML when connectors cross labels, branches are ambiguous, or text is too small. For a reference-style architecture diagram, favor a clean left-to-right or top-to-bottom composition over adding more nodes.
6. Validate before handoff: run `xmllint --noout <file>` when available, verify every edge's `source` and `target` refers to an existing cell, and confirm the file is a valid editable Draw.io document. If the diagram is opened through MCP, report the generated editor URL as well as the saved file path.

## Visual Rules

- Separate semantic flows. Use one color for data movement, another for control or scheduling, and a third for the final output. Use dashed lines for asynchronous handoff or a logical association, not for a second copy of the same data flow.
- Do not connect multiple upstream stages directly to a final storage box when that makes ownership unclear. Insert an explicit queue, worker, or transformation stage when it is the actual intermediary.
- For pipelines, use two or more labeled lanes. Show at least two or three staggered work items when overlap matters, and make the overlap visible as timing or position, not merely as a paragraph.
- Distinguish a single worker from a worker pool. Never draw one box per thread unless the implementation really creates independent workers.
- Keep API names in monospace and use `()` without long parameter lists. Show only the data structures that explain the design; do not turn the diagram into a source-code inventory.
- Use short labels, generous spacing, and large fonts. Move caveats such as alignment fallback or optional branches to a small note near the relevant path.
- When an image contains ambiguous or overlapping connections, correct the structure in the recreated diagram and explain the correction briefly instead of reproducing the ambiguity.

## Common Layouts

For a layered architecture, use horizontal bands for user space, kernel/runtime, storage, and device output. For a cache, show a common key/lookup entry before the hit/miss branch, then represent the hash index, LRU chain, and eviction mechanism as separate visual elements. For an asynchronous I/O pipeline, use a top allocation/submission lane and a bottom worker/read lane; only the worker/read lane should carry file data into the final buffer, while the allocation lane produces pages or work items and hands them to the worker.

## Handoff

Return the absolute path to the editable `.drawio` file, a short statement of what the main arrows mean, and any important modeling assumption. Do not claim that a diagram was opened or visually checked unless the MCP call actually succeeded. If only XML validation was possible, say so explicitly.
