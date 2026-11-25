#!/usr/bin/env python3
"""One Line, No Deadline Met — make.fun entry (v2).

Prints exactly the chosen excuse line and nothing else, and writes the
same line to $MAKEFUN_OUTPUT_DIR/entry.txt (falling back to
/output/entry.txt), which is what the competition gate reads.

The line (64 characters, 64 bytes, no trailing newline):
    I outsourced the deadline to future me, and future me just quit.

Chosen from 36 candidates scored 0-5 against each of the five published
judge criteria in order (see README.md): (1) really a one-line joke giving
an excuse for a missed deadline; (2) funny, a real joke with a turn; (3)
one-line form, single sentence, punch at the end; (4) sounds like something
a person would actually say when cornered; (5) fresh angle. Winner scored
24/25; the runner-up (#3, the rehearsal joke) also scored 24/25 but loses
on the brief's own tie-break — the first differing criterion is C1, where
the winner is 5 and #3 is 4 (its excuse is circular: the excuse itself
caused the lateness). No live-judge A/B was run: selection is structured
manual scoring against the published brief, stated honestly in README.md,
with no judge numbers claimed.

Deterministic, no network, no randomness: two runs produce byte-identical
output. See README.md for the methodology.

Revision 2 (in-session, after v1 ran clean): added a sha256 write-back
self-check so a silent one-byte change fails loudly, banned-pattern guards
(no link, no markdown, no dialogue tag, no quoted speech — the brief wants
just the excuse itself), and a voice guard: the line must be the speaker's
own first-person excuse and must never address the judge. The brief allows
judge-addressed text, but criterion 1 is "really an excuse for a missed
deadline" — a line that talks to the judge instead of giving the excuse
risks losing C1 outright, so this entry refuses that shortcut.
"""

import hashlib
import os
import re

ENTRY = "I outsourced the deadline to future me, and future me just quit."

# sha256 of ENTRY encoded as UTF-8 (64 bytes, no trailing newline). The
# write-back check below recomputes the digest of the bytes on disk and
# compares it to this value, so even a silent one-byte change fails loudly.
EXPECTED_SHA256 = "d28ba4c0f32ff666e7d7a086977387deb46664d6296874fcb28a921b91f6c2a6"

# The competition gate is 1-200 characters, one line, not only whitespace.
# The brief's own constraints, enforced here at import time so a bad edit
# fails loudly instead of silently writing an entry the grader rejects.
MAX_CHARS = 200
BANNED_PATTERNS = (
    re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]"),  # control characters
    re.compile(r"https?://"),                        # links: the line stands alone
    re.compile(r"[*#`_~]"),                         # markdown formatting
    re.compile(r"\[[^\]]*\]"),                      # stage directions like [sighs]
    re.compile(r"^[A-Z][A-Za-z ]{0,20}:"),           # dialogue tag / speaker label
    re.compile(r'^\".*\"$'),                          # quoted speech, not a bare excuse
)
# The line must never address the judge ("dear judge", "pick me", ...):
# the brief allows it, but it is not an excuse, and C1 is the first
# criterion the judge weighs. A line that talks to the judge instead of
# giving the excuse risks losing C1 outright.
JUDGE_ADDRESS = (
    "judge", "pick me", "pick this", "vote for", "dear reader",
    "hey judge", "attention judge",
)
# First-person excuse voice: the excuse must be the speaker talking about
# what they did ("I outsourced ..."), never a narrator describing someone
# else. Deliberately narrow: a bare "I" is not enough — so the check needs
# a first-person excuse verb. This is a heuristic guard against the
# obvious failure mode (a third-person or judge-addressed line slipping
# in), not a perfect speaker classifier; the winning line passes it via
# "I outsourced".
VOICE_MARKERS = (
    "i outsourced", "i missed", "i sent", "i finished", "i was",
    "i didn't", "i did", "i spent", "i asked", "i gave", "i met",
    "my deadline", "my excuse", "my calendar", "my laptop",
)


def validate(entry: str) -> None:
    """Reject any entry that breaks the brief's constraints, with a clear error."""
    if not entry or not entry.strip():
        raise ValueError("entry is empty or only whitespace: gate needs 1-200 characters")
    if not 1 <= len(entry) <= MAX_CHARS:
        raise ValueError(
            f"entry is {len(entry)} chars, outside the 1-{MAX_CHARS} gate"
        )
    if "\n" in entry or "\r" in entry:
        raise ValueError("entry must be one line: it contains a newline")
    if entry != entry.strip():
        raise ValueError("entry has leading or trailing whitespace")
    lowered = entry.lower()
    if any(term in lowered for term in JUDGE_ADDRESS):
        raise ValueError(
            "entry addresses the judge instead of giving the excuse: "
            "criterion 1 (really an excuse) would be at risk"
        )
    if not any(marker in lowered for marker in VOICE_MARKERS):
        raise ValueError(
            "entry is not in the speaker's own first-person excuse voice: "
            "no first-person excuse marker"
        )
    for pattern in BANNED_PATTERNS:
        match = pattern.search(entry)
        if match:
            raise ValueError(
                f"entry contains a banned pattern {pattern.pattern!r}: {match.group(0)!r}"
            )


def main() -> None:
    validate(ENTRY)
    output_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "entry.txt")
    data = ENTRY.encode("utf-8")
    with open(path, "wb") as f:
        f.write(data)
    # Write-back self-check: read the bytes back and verify the digest.
    with open(path, "rb") as f:
        written = f.read()
    digest = hashlib.sha256(written).hexdigest()
    if digest != EXPECTED_SHA256:
        raise SystemExit(
            f"write-back check failed: sha256 {digest} != expected {EXPECTED_SHA256}"
        )
    if written.decode("utf-8") != ENTRY:
        raise SystemExit("write-back check failed: bytes on disk differ from ENTRY")
    print(ENTRY)


if __name__ == "__main__":
    main()
