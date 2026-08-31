# Himma core truth

- Product name: **هِمّة**. Tagline: **أتعلم، أتطور، أصل إلى القمة**.
- Research web platform for up to 15 grade-three learners with reading difficulties in Oman.
- Arabic RTL, responsive on mobile, tablet, and desktop. No native mobile app in scope.
- Roles: student and researcher/admin. Students are created by the researcher and sign in with a unique simple code; no child self-registration or email.
- Core flow: pre-test (30) -> initial level -> adaptive activities -> researcher-enabled post-test (30) -> comparison and reports.
- Levels: readiness for reading; word building; fluency and comprehension.
- Content: 10 core + 5 conditional reinforcement activities per level (45 total).
- Adaptation: use the latest three valid attempts weighted 50/30/20. Invalid, incomplete, failed, or low-confidence audio attempts never affect score or adaptation.
- Promote at weighted mastery >=80% with required skill coverage and no critical skill <60%; support first below 50%; demote one level only after two consecutive low decisions; manual override requires reason and audit history.
- Student UI: one instruction, one task, one primary action per screen. Never label a child weak or show research diagnostics.
- Approved colors: blue `#347FD9`, green `#51B985`, yellow `#FFC857`, navy `#20364D`, light `#F7FBFF`, border `#DCE8F2`.
- Typography: Tajawal for child UI; IBM Plex Sans Arabic for researcher UI and reports; Noto Sans Arabic fallback.
- Approved prerecorded audio package: `assets/audio/HIMMA_AUDIO_V1/` with 50 stable content IDs and 100 binaries (50 WAV masters + 50 MP3 web files): 4 feedback, 6 letter sounds, 12 syllables, and 28 words. Its `manifest.csv` is the current audio source of truth.
- The 10 `INS-*` instruction scripts remain in historical planning references but are not part of the approved HIMMA_AUDIO_V1 binary delivery. Do not synthesize or claim them as delivered without a new recorded package and decision.
- `reference/original/` and `reference/ui-prototype/` are read-only. The prototype is visual/interaction reference, not production architecture or domain truth.
- Resolve reference precedence through `docs/specs/SOURCE_OF_TRUTH.md`; do not choose between same-numbered legacy documents by filename alone.
- Every content item and asset uses a stable technical ID. Do not rename approved assets after they are linked.
- Do not claim medical/educational diagnosis or guaranteed speech accuracy.
