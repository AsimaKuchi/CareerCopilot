import { Document, Packer, Paragraph, TextRun } from "docx";
import { saveAs } from "file-saver";
import { jsPDF } from "jspdf";

const safeFilename = (name, ext = "docx") => {
  const cleaned = (name || "document")
    .replace(/[<>:"/\\|?*]/g, "_")
    .replace(/[\x00-\x1F]/g, "")
    .trim();

  return cleaned.toLowerCase().endsWith(`.${ext}`) ? cleaned : `${cleaned}.${ext}`;
};

/**
 * Download text content as a PDF file
 */
export function downloadPdfFromText(text, filename) {
  if (!text) {
    console.error("[downloadPdfFromText] No text provided");
    return;
  }

  try {
    console.log("[downloadPdfFromText] Starting PDF generation...");
    const doc = new jsPDF();
    const pageWidth = doc.internal.pageSize.getWidth();
    const margin = 20;
    const maxWidth = pageWidth - margin * 2;
    
    const lines = doc.splitTextToSize(text, maxWidth);
    
    let y = margin;
    const lineHeight = 7;
    const pageHeight = doc.internal.pageSize.getHeight();
    
    lines.forEach((line) => {
      if (y + lineHeight > pageHeight - margin) {
        doc.addPage();
        y = margin;
      }
      doc.text(line, margin, y);
      y += lineHeight;
    });
    
    doc.save(safeFilename(filename, "pdf"));
    console.log("[downloadPdfFromText] PDF downloaded successfully");
  } catch (error) {
    console.error("[downloadPdfFromText] Error:", error);
    alert("Failed to download PDF: " + error.message);
  }
}

/**
 * Download text content as a DOCX file
 */
export async function downloadDocxFromText(text, filename) {
  if (!text) {
    console.error("[downloadDocxFromText] No text provided");
    alert("No content to download");
    return;
  }

  try {
    console.log("[downloadDocxFromText] Starting DOCX generation...");
    const paragraphs = text
      .split(/\n\s*\n/)
      .map(
        (block) =>
          new Paragraph({
            children: [
              new TextRun({
                text: block,
                size: 24,
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
    console.log("[downloadDocxFromText] Blob created, size:", blob.size);
    saveAs(blob, safeFilename(filename, "docx"));
    console.log("[downloadDocxFromText] DOCX downloaded successfully");
  } catch (error) {
    console.error("[downloadDocxFromText] Error:", error);
    console.log("[downloadDocxFromText] Falling back to PDF...");
    downloadPdfFromText(text, filename.replace(/\.docx$/i, ""));
  }
}
