import { Document, Packer, Paragraph, TextRun } from "docx";
import { saveAs } from "file-saver";

export async function downloadDocxFromText(
  text: string,
  filename: string
) {
  if (!text) return;

  const paragraphs = text
    .split(/\n\s*\n/)
    .map(
      (block) =>
        new Paragraph({
          children: [
            new TextRun({
              text: block,
              size: 24, // 12pt
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
  saveAs(blob, filename);
}
