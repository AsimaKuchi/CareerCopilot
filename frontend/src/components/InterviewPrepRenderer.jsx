/**
 * InterviewPrepRenderer.jsx
 *
 * Parses the deeply-structured markdown produced by /api/ai/interview-prep
 * (see backend/routes/ai_routes.py) and renders it as scannable interview
 * prep cards.
 *
 * Handled document shape:
 *   # Title
 *   ## 1. HOW TO STRUCTURE YOUR THINKING   <- primer (bullet list)
 *   ## 2. COMMON INTERVIEW QUESTIONS       <- Q&A block section
 *   ## 3. BEHAVIORAL QUESTIONS             <- Q&A block section
 *   ## 4. TECHNICAL / ROLE-SPECIFIC ...    <- Q&A block section
 *   ## 5. CURVEBALL & JUDGMENT QUESTIONS   <- Q&A block section
 *   ## 6. INTERVIEW TIPS                   <- numbered list
 *   ## 7. QUESTIONS TO ASK THE INTERVIEWER <- numbered list
 *
 * Per-question fields:
 *   #### Question text
 *   - Difficulty: Easy | Medium | Hard | Curveball
 *   - What they're testing: ...
 *   - Likely follow-ups:
 *     * sub-bullet
 *   - Traps to avoid: ...
 *   - How to structure your answer:
 *     * sub-bullet
 *   > Sample answer paragraph
 *
 * Resilient to partial markdown - safe to call mid-stream while tokens are
 * still arriving.
 */
import React from "react";
import { AlertTriangle, ListChecks, Target, MessageCircle } from "lucide-react";

const SECTION_KIND = {
  PRIMER: "primer",
  QA: "qa",
  LIST: "list",
};

// Section number -> render kind
const sectionKindFor = (number) => {
  if (number === 1) return SECTION_KIND.PRIMER;
  if (number >= 6) return SECTION_KIND.LIST;
  return SECTION_KIND.QA;
};

// Match a field label at start of a bullet line, e.g. "- Difficulty: Easy"
// Returns { label, value } or null.
function matchField(line) {
  const stripped = line.replace(/^[-•*]\s*/, "");
  const m = stripped.match(/^([A-Za-z][A-Za-z' \-/]{2,40}?):\s*(.*)$/);
  if (!m) return null;
  return { label: m[1].trim().toLowerCase(), value: m[2].trim() };
}

function newQAItem(question) {
  return {
    question,
    difficulty: null,
    testing: null,
    followups: [], // strings
    traps: null,
    approach: [], // strings (bullets)
    sample: [], // strings (blockquote lines)
  };
}

function parsePrepDocument(markdown) {
  if (!markdown) return { sections: [] };

  const lines = markdown.split("\n");
  const sections = [];
  let currentSection = null;
  let currentItem = null;
  // Which sub-field of currentItem should trailing bullets append to?
  // Values: null | "followups" | "approach"
  let subState = null;

  const flushItem = () => {
    if (currentItem && currentSection) {
      currentSection.items.push(currentItem);
    }
    currentItem = null;
    subState = null;
  };

  const flushSection = () => {
    flushItem();
    if (currentSection) sections.push(currentSection);
    currentSection = null;
  };

  for (const raw of lines) {
    const line = raw.trim();
    if (!line || line === "---" || line === "___") continue;

    // Section header: "## 1. TITLE", "# 1. TITLE", or bare "1. TITLE"
    // Title can contain letters, digits, spaces, "/", "&", "-"
    const sectionMatch = line.match(
      /^#{0,3}\s*(\d+)\.\s+([A-Z][A-Z0-9 /&\-]+)$/
    );
    if (sectionMatch) {
      flushSection();
      const number = parseInt(sectionMatch[1], 10);
      const title = sectionMatch[2].trim();
      currentSection = {
        number,
        title,
        items: [],
        kind: sectionKindFor(number),
      };
      continue;
    }

    // Skip stray "# Document Title" before first numbered section
    if (line.startsWith("# ") && !currentSection) continue;
    if (!currentSection) continue;

    // Question marker (only meaningful in Q&A sections)
    if (line.startsWith("####")) {
      flushItem();
      const qText = line.replace(/^#+\s*/, "").trim();
      if (currentSection.kind === SECTION_KIND.QA) {
        currentItem = newQAItem(qText);
      }
      continue;
    }

    // ----- PRIMER SECTION -----
    if (currentSection.kind === SECTION_KIND.PRIMER) {
      // Framework header line like "* STAR (Situation, Task, Action, Result)"
      // or bullet "- Something".  Store everything as bullets.
      const cleaned = line
        .replace(/^>\s*/, "")
        .replace(/^[-•*]\s*/, "")
        .replace(/^\d+\.\s*/, "")
        .trim();
      if (cleaned) currentSection.items.push({ text: cleaned });
      continue;
    }

    // ----- LIST SECTION (Tips, Questions to Ask) -----
    if (currentSection.kind === SECTION_KIND.LIST) {
      const numMatch = line.match(/^(\d+)\.\s+(.*)/);
      if (numMatch) {
        flushItem();
        currentItem = { text: numMatch[2].trim(), continuation: [] };
      } else if (currentItem) {
        currentItem.continuation.push(
          line.replace(/^[>\-•*]\s*/, "").trim()
        );
      }
      continue;
    }

    // ----- Q&A SECTION -----
    if (!currentItem) continue;

    // Blockquote -> sample answer
    if (line.startsWith(">")) {
      const txt = line.replace(/^>\s*/, "").trim();
      if (txt) currentItem.sample.push(txt);
      subState = null;
      continue;
    }

    // Try to match a labelled field like "- Difficulty: Easy"
    const field = matchField(line);
    if (field) {
      const { label, value } = field;
      if (label === "difficulty") {
        currentItem.difficulty = value;
        subState = null;
        continue;
      }
      if (label === "what they're testing" || label === "what theyre testing") {
        currentItem.testing = value;
        subState = null;
        continue;
      }
      if (label === "likely follow-ups" || label === "likely followups") {
        subState = "followups";
        // Some models put the first item on the same line
        if (value) currentItem.followups.push(value);
        continue;
      }
      if (label === "traps to avoid" || label === "traps") {
        currentItem.traps = value;
        subState = null;
        continue;
      }
      if (
        label === "how to structure your answer" ||
        label === "structure your answer" ||
        label === "suggested approach" ||
        label === "approach"
      ) {
        subState = "approach";
        if (value) currentItem.approach.push(value);
        continue;
      }
    }

    // Sub-bullet under an active subState
    const bulletMatch = line.match(/^[-•*]\s+(.+)/) || line.match(/^\*\s+(.+)/);
    if (bulletMatch) {
      const txt = bulletMatch[1].trim();
      if (subState === "followups") {
        currentItem.followups.push(txt);
        continue;
      }
      if (subState === "approach") {
        currentItem.approach.push(txt);
        continue;
      }
      // Un-scoped bullet -> treat as extra approach detail if we've started one,
      // otherwise as a general note.
      if (currentItem.approach.length > 0) {
        currentItem.approach.push(txt);
      } else {
        currentItem.sample.push(txt);
      }
      continue;
    }

    // Free-floating paragraph after sample already opened -> sample continuation
    if (currentItem.sample.length > 0) {
      currentItem.sample.push(line);
    }
  }

  flushSection();
  return { sections };
}

// ---------- Presentational helpers ----------

const DIFFICULTY_STYLES = {
  easy: "bg-emerald-50 text-emerald-700 border-emerald-200",
  medium: "bg-amber-50 text-amber-700 border-amber-200",
  hard: "bg-rose-50 text-rose-700 border-rose-200",
  curveball: "bg-purple-50 text-purple-700 border-purple-200",
};

const DifficultyBadge = ({ difficulty }) => {
  if (!difficulty) return null;
  const key = difficulty.toLowerCase().split(/[^a-z]/)[0];
  const cls = DIFFICULTY_STYLES[key] || "bg-slate-50 text-slate-700 border-slate-200";
  return (
    <span
      className={`inline-flex items-center text-[11px] font-semibold uppercase tracking-wide px-2 py-0.5 rounded border ${cls}`}
      data-testid="difficulty-badge"
    >
      {difficulty}
    </span>
  );
};

const FieldRow = ({ icon: Icon, iconClass, label, children, testid }) => (
  <div className="flex gap-3" data-testid={testid}>
    <div
      className={`w-7 h-7 rounded-md flex items-center justify-center flex-shrink-0 mt-0.5 ${iconClass}`}
    >
      <Icon className="w-4 h-4" />
    </div>
    <div className="flex-1 min-w-0">
      <p className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1">
        {label}
      </p>
      {children}
    </div>
  </div>
);

const QABlock = ({ item }) => {
  const hasStructure =
    item.difficulty ||
    item.testing ||
    item.followups.length > 0 ||
    item.traps ||
    item.approach.length > 0 ||
    item.sample.length > 0;

  return (
    <div className="rounded-xl overflow-hidden border border-slate-200 shadow-sm bg-white">
      {/* Question header */}
      <div className="bg-gradient-to-r from-indigo-50 to-slate-50 px-5 py-4 border-b border-slate-200">
        <div className="flex items-start gap-3">
          <span className="bg-indigo-600 text-white text-xs font-bold px-2.5 py-1 rounded flex-shrink-0">
            Q
          </span>
          <div className="flex-1 min-w-0">
            <p className="text-slate-900 font-bold leading-relaxed text-base">
              {item.question}
            </p>
            {item.difficulty && (
              <div className="mt-2">
                <DifficultyBadge difficulty={item.difficulty} />
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Body */}
      <div className="px-5 py-4 space-y-4">
        {item.testing && (
          <FieldRow
            icon={Target}
            iconClass="bg-blue-50 text-blue-600"
            label="What they're testing"
            testid="prep-testing"
          >
            <p className="text-slate-700 leading-relaxed text-sm">
              {item.testing}
            </p>
          </FieldRow>
        )}

        {item.followups.length > 0 && (
          <FieldRow
            icon={MessageCircle}
            iconClass="bg-slate-100 text-slate-600"
            label="Likely follow-ups"
            testid="prep-followups"
          >
            <ul className="space-y-1.5">
              {item.followups.map((f, i) => (
                <li
                  key={i}
                  className="text-slate-700 leading-relaxed text-sm flex gap-2"
                >
                  <span className="text-slate-400 mt-0.5">–</span>
                  <span>{f}</span>
                </li>
              ))}
            </ul>
          </FieldRow>
        )}

        {item.traps && (
          <FieldRow
            icon={AlertTriangle}
            iconClass="bg-rose-50 text-rose-600"
            label="Traps to avoid"
            testid="prep-traps"
          >
            <p className="text-slate-700 leading-relaxed text-sm font-medium">
              {item.traps}
            </p>
          </FieldRow>
        )}

        {item.approach.length > 0 && (
          <FieldRow
            icon={ListChecks}
            iconClass="bg-indigo-50 text-indigo-600"
            label="How to structure your answer"
            testid="prep-approach"
          >
            <ul className="space-y-1.5">
              {item.approach.map((a, i) => (
                <li
                  key={i}
                  className="text-slate-700 leading-relaxed text-sm flex gap-2"
                >
                  <span className="text-indigo-500 font-bold mt-0.5">•</span>
                  <span>{a}</span>
                </li>
              ))}
            </ul>
          </FieldRow>
        )}

        {item.sample.length > 0 && (
          <div className="border-t border-slate-100 pt-4">
            <div className="flex items-start gap-3">
              <span className="bg-emerald-600 text-white text-xs font-bold px-2.5 py-1 rounded flex-shrink-0">
                A
              </span>
              <div className="flex-1 min-w-0">
                <p className="text-[11px] font-bold uppercase tracking-wider text-emerald-700 mb-2">
                  Sample answer
                </p>
                <div className="border-l-4 border-emerald-500 bg-emerald-50/50 pl-4 py-2 rounded-r space-y-2">
                  {item.sample.map((s, i) => (
                    <p
                      key={i}
                      className="text-slate-700 leading-relaxed text-sm italic"
                    >
                      {s}
                    </p>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {!hasStructure && (
          <p className="text-slate-500 italic text-sm">
            Prepare your own answer based on your experience.
          </p>
        )}
      </div>
    </div>
  );
};

const ListBlock = ({ items }) => (
  <ol className="list-decimal pl-6 space-y-3 bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
    {items.map((it, idx) => (
      <li key={idx} className="text-slate-800 leading-relaxed">
        <span className="font-semibold">{it.text}</span>
        {it.continuation && it.continuation.length > 0 && (
          <div className="mt-1 text-sm text-slate-600">
            {it.continuation.join(" ")}
          </div>
        )}
      </li>
    ))}
  </ol>
);

const PrimerBlock = ({ items }) => (
  <div className="rounded-xl border border-indigo-200 bg-indigo-50/40 p-5 shadow-sm">
    <ul className="space-y-2">
      {items.map((it, idx) => {
        // Highlight framework name if the bullet starts with "STAR", "SBI", etc.
        const m = it.text.match(/^([A-Z]{3,7}|CIRCLES|MECE)\b(.*)/);
        return (
          <li
            key={idx}
            className="text-slate-800 leading-relaxed text-sm flex gap-2"
          >
            <span className="text-indigo-500 mt-1">•</span>
            <span>
              {m ? (
                <>
                  <span className="font-bold text-indigo-700">{m[1]}</span>
                  <span>{m[2]}</span>
                </>
              ) : (
                it.text
              )}
            </span>
          </li>
        );
      })}
    </ul>
  </div>
);

const SectionHeader = ({ number, title }) => (
  <div className="flex items-center gap-3 mb-4">
    <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center shadow-sm">
      <span className="text-white font-bold text-sm">{number}</span>
    </div>
    <h2 className="text-lg font-bold text-indigo-700 uppercase tracking-wide">
      {title}
    </h2>
  </div>
);

export default function InterviewPrepRenderer({ markdown }) {
  const { sections } = parsePrepDocument(markdown);

  // Fallback: parser couldn't recognize any structure yet (early stream)
  if (sections.length === 0) {
    return (
      <div className="bg-slate-50 rounded-xl p-6 border border-slate-200">
        <p className="text-slate-800 leading-relaxed whitespace-pre-wrap">
          {markdown}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8" data-testid="interview-prep-content">
      {sections.map((sec, i) => (
        <div key={i} data-testid={`prep-section-${sec.number}`}>
          <SectionHeader number={sec.number} title={sec.title} />
          {sec.kind === SECTION_KIND.PRIMER && <PrimerBlock items={sec.items} />}
          {sec.kind === SECTION_KIND.LIST && <ListBlock items={sec.items} />}
          {sec.kind === SECTION_KIND.QA && (
            <div className="space-y-4">
              {sec.items.map((item, idx) => (
                <QABlock key={idx} item={item} />
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
