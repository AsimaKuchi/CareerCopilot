import { Document, Packer, Paragraph, TextRun } from "docx";
import { saveAs } from "file-saver";

const safeFilename = (name) => {
  const cleaned = (name || "document.docx")
    .replace(/[<>:"/\\|?*\x00-\x1F]/g, "_")
    .trim();

  return cleaned.toLowerCase().endsWith(".docx") ? cleaned : `${cleaned}.docx`;
};

export async function downloadDocxFromText(text, filename) {
  if (!text) return;

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

  const doc = new Document({
    sections: [{ children: paragraphs }],
  });

  const blob = await Packer.toBlob(doc);
  saveAs(blob, safeFilename(filename));
}
