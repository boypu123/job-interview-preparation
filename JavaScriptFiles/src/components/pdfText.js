// pdfText.ts
import * as pdfjsLib from 'pdfjs-dist';
import pdfWorker from 'pdfjs-dist/build/pdf.worker.mjs?worker';

// Tell pdf.js where to find its worker
pdfjsLib.GlobalWorkerOptions.workerPort = new pdfWorker();

// Extract text from a PDF (ArrayBuffer)
export async function extractPdfText(arrayBuffer) {
  const loadingTask = pdfjsLib.getDocument({ data: arrayBuffer });
  const pdf = await loadingTask.promise;

  let fullText = '';

  for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
    const page = await pdf.getPage(pageNum);
    const content = await page.getTextContent();
    // Join in reading order
    const strings = content.items
      .map((item) => ('str' in item ? item.str : ''))
      .filter(Boolean);

    fullText += strings.join(' ') + '\n\n';
  }

  await pdf.cleanup();
  return fullText.trim();
}
