-- Add a return-link (↩) to every footnote so navigation is bidirectional
-- even on readers that don't support epub3 popup footnotes.
--
-- Pandoc's epub3 writer emits each note as <aside epub:type="footnote"
-- id="fnN"> and the in-text marker as <a id="fnrefN" ...>, and it RESETS
-- that numbering at every split boundary (here, each level-1 heading = one
-- book). So the back-link target fnref<N> must use the note's index WITHIN
-- its book, not a document-global counter.
--
-- We therefore walk the document in order ourselves: reset the per-book
-- counter at each level-1 Header, and number notes as we meet them, in the
-- exact top-to-bottom order the epub writer will use. pandoc.walk_block on
-- each top-level block visits its inline Notes in order.

local function backlink(n)
  return string.format(
    ' <a href="#fnref%d" class="footnote-back" role="doc-backlink"'
    .. ' epub:type="backlink">\u{21A9}</a>', n)
end

local function append_backlink(note, n)
  local blocks = note.content
  local last = blocks[#blocks]
  local raw = pandoc.RawInline("html", backlink(n))
  if last and (last.t == "Para" or last.t == "Plain") then
    table.insert(last.content, raw)
  else
    table.insert(blocks, pandoc.RawBlock("html", "<p>" .. backlink(n) .. "</p>"))
  end
  return pandoc.Note(blocks)
end

function Pandoc(doc)
  local counter = 0
  local new_blocks = {}
  for _, block in ipairs(doc.blocks) do
    -- A level-1 heading starts a new book -> Pandoc restarts fnref at 1.
    if block.t == "Header" and block.level == 1 then
      counter = 0
    end
    -- Number every Note inside this top-level block, in order.
    local walked = pandoc.walk_block(block, {
      Note = function(note)
        counter = counter + 1
        return append_backlink(note, counter)
      end,
    })
    table.insert(new_blocks, walked)
  end
  return pandoc.Pandoc(new_blocks, doc.meta)
end
