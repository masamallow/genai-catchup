// Marp CLI configuration (https://github.com/marp-team/marp-cli#configuration-file)
// Uses the locally installed Marp Core 5 with its Mermaid plugin, so ```mermaid fences
// become inline SVG at build time (beautiful-mermaid, no browser needed).
import { Marp } from '@marp-team/marp-core'
import mermaidPlugin from '@marp-team/marp-core/plugins/mermaid'

export default {
  engine: (opts) => new Marp(opts).use(mermaidPlugin()),
  html: true, // slides use <div class="grid"> / <div class="cols"> for layout
  themeSet: './themes',
  allowLocalFiles: false,
}
