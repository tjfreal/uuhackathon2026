# Presentation

Trails reconstructs the history of an idea from a corpus of text files.

It sits between retrieval and synthesis:

- you have years of notes scattered across hundreds of files
- you want to know how a topic developed, not just where it appears now
- you ask Trails for the arc of "3d scanning" or "design review" or "knowledge building"
- it finds every mention, extracts a date, pulls the relevant passage, and assembles a timeline

The most important thing about Trails is the question it asks the corpus:
not "what is relevant?" but "how did I get here?"

Throughline and Trails are complementary. Throughline surfaces what matters now.
Trails shows the path. Run both on the same topic and you get coverage plus history —
a heatmap of what you know, and a map of how you came to know it.

The current honest status is: real local `v1`, not a finished platform.

The CLI exists. It can already:

- search a text corpus by keyword
- extract dates from filenames, frontmatter, and inline ISO dates
- assemble one dated excerpt per file into a readable arc
- optionally use an embeddings index or ask for a prose narrative when those extras are available

Trails is not a journaling tool and not just a search tool. It is an archaeology tool.
The output is a dated arc that no single file in the corpus contains.
That arc is itself a new artifact — worth keeping, worth sharing, worth building from.

The larger reason it matters in this repo is that it makes the synthesis layer more explicit.
If Throughline helps answer "what matters here?" then Trails helps answer "what path led here?"
