import { Document, Packer, Paragraph, TextRun } from "docx";
import { saveAs } from "file-saver";

const safeFilename = (name) => {
  const cleaned = (name || "document.docx")
    .replace(/[<>:"/\\|?*\x00-\x1F]/g, "_")
    .trim();

  return cleaned.toLowerCase().endsWith(".docx") ? cleaned : `${cleaned}.docx`;
};

export async function downloadDocxFromText(text, filename) {
  console.log("[downloadDocxFromText] Starting download...", { textLength: text?.length, filename });
  
  if (!text) {
    console.error("[downloadDocxFromText] No text provided");
    return;
  }

  try {
    console.log("[downloadDocxFromText] Creating paragraphs...");
    const paragraphs = text
      .split(/\n\s*\n/)
      .map(
        (block) =>
          new Paragraph({
            children: [
              new TextRun({
                text: block,
                size: 24, // 12pt (docx uses half-points)
                font: "Calibri",
              }),
            ],
            spacing: { after: 200 },
          })
      );

    console.log("[downloadDocxFromText] Creating document with", paragraphs.length, "paragraphs");
    const doc = new Document({
      sections: [{ children: paragraphs }],
    });

    console.log("[downloadDocxFromText] Packing to blob...");
    const blob = await Packer.toBlob(doc);
    console.log("[downloadDocxFromText] Blob created, size:", blob.size);

    const safeName = safeFilename(filename);
    console.log("[downloadDocxFromText] Calling saveAs with filename:", safeName);
    saveAs(blob, safeName);
    console.log("[downloadDocxFromText] saveAs called successfully");
  } catch (error) {
    console.error("[downloadDocxFromText] Error:", error);
    console.error("[downloadDocxFromText] Error stack:", error.stack);
  }
}
