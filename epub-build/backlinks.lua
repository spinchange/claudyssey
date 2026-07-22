-- Make footnotes render CONSISTENTLY across every e-reader, not just the
-- ones that support epub3 popup footnotes.
--
-- Pandoc's epub3 writer emits each note as <aside epub:type="footnote"
-- id="fnN"> and the marker as <a id="fnrefN" ...>. Two problems that caused
-- cross-platform inconsistency:
--   1. The note's visible NUMBER came from CSS: aside::before{content:counter}.
--      Kindle conversion (and some engines) strip the epub:type attribute the
--      selector matched, so the notes lost their numbers and read as an
--      unnumbered run of paragraphs.
--   2. The return arrow was the only way back on non-popup readers.
-- Fix: bake BOTH the number and the back-arrow into the note's content as
-- real inline elements. They survive conversion and render the same whether
-- the note is shown as a popup or as an end-of-chapter endnote.
--
-- Pandoc RESETS fnref numbering at every split boundary (each level-1 heading
-- = one book), so we keep a per-book counter, walking the document in order.

-- The clickable number that opens the note stays the same (Pandoc's noteref).
-- Inside the note we prepend "N." linking back to the marker, and (belt and
-- suspenders) also append a return arrow. Both point to #fnref<N>.
local function num_prefix(n)
  return string.format(
    '<a href="#fnref%d" class="fn-num" role="doc-backlink" epub:type="backlink">'
    .. '%d.</a> ', n, n)
end

local function back_arrow(n)
  return string.format(
    ' <a href="#fnref%d" class="footnote-back" role="doc-backlink"'
    .. ' epub:type="backlink">\u{21A9}</a>', n)
end

local function decorate(note, n)
  local blocks = note.content
  -- Prepend the visible, linked number to the first paragraph.
  local first = blocks[1]
  if first and (first.t == "Para" or first.t == "Plain") then
    table.insert(first.content, 1, pandoc.RawInline("html", num_prefix(n)))
  else
    table.insert(blocks, 1, pandoc.RawBlock("html", num_prefix(n)))
  end
  -- Append the return arrow to the last paragraph.
  local last = blocks[#blocks]
  if last and (last.t == "Para" or last.t == "Plain") then
    table.insert(last.content, pandoc.RawInline("html", back_arrow(n)))
  else
    table.insert(blocks, pandoc.RawBlock("html", "<p>" .. back_arrow(n) .. "</p>"))
  end
  return pandoc.Note(blocks)
end

function Pandoc(doc)
  local counter = 0
  local new_blocks = {}
  for _, block in ipairs(doc.blocks) do
    if block.t == "Header" and block.level == 1 then
      counter = 0
    end
    local walked = pandoc.walk_block(block, {
      Note = function(note)
        counter = counter + 1
        return decorate(note, counter)
      end,
    })
    table.insert(new_blocks, walked)
  end
  return pandoc.Pandoc(new_blocks, doc.meta)
end
