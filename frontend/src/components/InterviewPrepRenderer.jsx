/**
 * InterviewPrepRenderer.jsx
 *
 * Parses the structured markdown produced by /api/ai/interview-prep into:
 *   - Sectioned Q&A blocks (Common, Behavioral, Technical) using `####` as
 *     the question marker so wording like "Tell me about a time..." (no `?`)
 *     is still recognized as a question.
 *   - Plain numbered-list sections (Interview Tips, Questions to Ask).
 *
 * Resilient to partial markdown - safe to call mid-stream while tokens are
 * still arriving.
 */
import React from "react";

function parsePrepDocument(markdown) {
  if (!markdown) return { sections: [] };

  const lines = markdown.split("\n");
  const sections = [];
  let currentSection = null;
  let currentItem = null; // current Q&A item OR a list-item placeholder

  const flushItem = () => {
    if (currentItem && currentSection) {
      currentSection.items.push(currentItem);
    }
    currentItem = null;
  };

  const flushSection = () => {
    flushItem();
    if (currentSection) sections.push(currentSection);
    currentSection = null;
  };

  for (const raw of lines) {
    const line = raw.trim();
    if (!line || line === "---" || line === "___") continue;

    // Section header: "## 1. SECTION TITLE", "# SECTION TITLE", "1. SECTION TITLE"
    const sectionMatch = line.match(/^#{0,3}\s*(\d+)\.\s+([A-Z][A-Z\s&]+)$/);
    if (sectionMatch) {
      flushSection();
      const number = parseInt(sectionMatch[1], 10);
      const title = sectionMatch[2].trim();
      // Sections 4 (TIPS) and 5 (QUESTIONS TO ASK) are simple lists,
      // everything else uses Q&A blocks.
      const isList = number >= 4;
      currentSection = { number, title, items: [], isList };
      continue;
    }

    // Skip the document title (single # at start)
    if (line.startsWith("# ") && !currentSection) continue;

    // No section yet -> skip stray lines before first section header
    if (!currentSection) continue;

    // Question marker: `#### question text`
    if (line.startsWith("####")) {
      flushItem();
      const qText = line.replace(/^#+\s*/, "").trim();
      currentItem = { question: qText, approach: null, answer: [] };
      continue;
    }

    if (currentSection.isList) {
      // List section: each numbered item becomes one entry
      const listMatch = line.match(/^(\d+)\.\s+(.*)/);
      if (listMatch) {
        flushItem();
        currentItem = { text: listMatch[2].trim(), continuation: [] };
      } else if (currentItem) {
        // Continuation of a previous list item (rare but possible)
        currentItem.continuation.push(line.replace(/^[-•*>]\s*/, ""));
      }
      continue;
    }

    // Q&A section content
    if (!currentItem) continue;

    const lower = line.toLowerCase();
    const isApproach =
      lower.startsWith("suggested approach:") ||
      lower.startsWith("approach:") ||
      lower.includes("star framework") ||
      lower.includes("framework guidance");

    if (isApproach && !currentItem.approach) {
      currentItem.approach = line
        .replace(/^>\s*/, "")
        .replace(/^[-•*]\s*/, "")
        .replace(/^suggested approach[:\s-]*/i, "")
        .replace(/^approach[:\s-]*/i, "")
        .trim();
      continue;
    }

    // Everything else is answer body. Strip markdown bullet/blockquote
    // markers and store as a paragraph.
    const cleaned = line
      .replace(/^>\s*/, "")
      .replace(/^[-•*]\s*/, "")
      .replace(/^\d+\.\s*/, "")
      .trim();
    if (cleaned) currentItem.answer.push(cleaned);
  }

  flushSection();
  return { sections };
}

const QABlock = ({ item }) => (
  <div className="rounded-xl overflow-hidden border border-slate-200 shadow-sm">
    <div className="bg-slate-50 px-5 py-4">
      <div className="flex items-start gap-3">
        <span className="bg-indigo-500 text-white text-xs font-bold px-2.5 py-1 rounded flex-shrink-0">
          Q
        </span>
        <p className="text-slate-900 font-semibold leading-relaxed">{item.question}</p>
      </div>
    </div>
    <div className="bg-white px-5 py-4 border-t border-slate-100">
      <div className="flex items-start gap-3">
        <span className="bg-emerald-500 text-white text-xs font-bold px-2.5 py-1 rounded flex-shrink-0">
          A
        </span>
        <div className="space-y-3 flex-1">
          {item.approach && (
            <p className="text-slate-700 font-medium italic">{item.approach}</p>
          )}
          {item.answer.map((line, lIdx) => (
            <p key={lIdx} className="text-slate-700 leading-relaxed">
              {line}
            </p>
          ))}
          {item.answer.length === 0 && !item.approach && (
            <p className="text-slate-500 italic">
              Prepare your own answer based on your experience.
            </p>
          )}
        </div>
      </div>
    </div>
  </div>
);

const ListBlock = ({ items }) => (
  <ol className="list-decimal pl-6 space-y-3 bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
    {items.map((it, idx) => (
      <li key={idx} className="text-slate-800 leading-relaxed">
        {it.text}
        {it.continuation?.length > 0 && (
          <div className="mt-1 text-sm text-slate-600">
            {it.continuation.join(" ")}
          </div>
        )}
      </li>
    ))}
  </ol>
);

export default function InterviewPrepRenderer({ markdown }) {
  const { sections } = parsePrepDocument(markdown);

  // If parser couldn't recognize structure, fall back to plain pre.
  if (sections.length === 0) {
    return (
      <div className="bg-slate-50 rounded-xl p-6 border border-slate-200">
        <p className="text-slate-800 leading-relaxed whitespace-pre-wrap">{markdown}</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {sections.map((sec, i) => (
        <div key={i} data-testid={`prep-section-${sec.number}`}>
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 rounded-lg bg-indigo-500 flex items-center justify-center shadow-sm">
              <span className="text-white font-bold text-sm">{sec.number}</span>
            </div>
            <h2 className="text-lg font-bold text-indigo-600 uppercase tracking-wide">
              {sec.title}
            </h2>
          </div>
          {sec.isList ? (
            <ListBlock items={sec.items} />
          ) : (
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
