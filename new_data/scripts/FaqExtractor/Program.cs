using DocumentFormat.OpenXml;
using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Wordprocessing;
using System.Text;
using System.Text.RegularExpressions;

// Input and output paths
var inputPath = @"D:\ai_assistant\new_data\Часто задаваемые вопросы ответы  КЦ ТПП 2026.docx";
var outputCsv = @"D:\ai_assistant\new_data\source\operational\faq\faq-kt-tpp-2026.csv";
var outputMd = @"D:\ai_assistant\new_data\source\markdown_data\faq-kt-tpp-2026.md";

// Ensure output directories exist
Directory.CreateDirectory(Path.GetDirectoryName(outputCsv)!);
Directory.CreateDirectory(Path.GetDirectoryName(outputMd)!);

// Read the document
var doc = WordprocessingDocument.Open(inputPath, false);
var body = doc.MainDocumentPart!.Document.Body!;

// Find the main table with Q&A
var tables = body.Elements<Table>().ToList();
Console.WriteLine($"Found {tables.Count} tables");

var qaPairs = new List<(string Question, string Answer)>();

foreach (var table in tables)
{
    var rows = table.Elements<TableRow>().ToList();
    Console.WriteLine($"Table has {rows.Count} rows");
    
    // Skip header row (row 0), process data rows from row 1 onwards
    for (int i = 1; i < rows.Count; i++)
    {
        var row = rows[i];
        var cellList = row.Elements<TableCell>().ToList();
        
        if (cellList.Count >= 3)
        {
            var num = cellList[0].InnerText.Trim();
            var question = cellList[1].InnerText.Trim();
            var answer = cellList[2].InnerText.Trim();
            
            // Skip if question cell is empty or is header-like
            if (string.IsNullOrWhiteSpace(question))
                continue;
            
            // Skip header row content
            if (question.ToLower().Contains("вопрос") || num == "№")
                continue;
            
            qaPairs.Add((question, answer));
        }
    }
}

Console.WriteLine($"\nTotal Q&A pairs found: {qaPairs.Count}");

// Generate CSV
var csv = new StringBuilder();
csv.AppendLine("question;answer;category;source");
foreach (var (q, a) in qaPairs)
{
    // Escape fields containing semicolons or newlines by wrapping in quotes
    var qEscaped = q.Contains(';') || q.Contains('\n') || q.Contains('"') ? $"\"{q.Replace("\"", "\"\"")}\"" : q;
    var aEscaped = a.Contains(';') || a.Contains('\n') || a.Contains('"') ? $"\"{a.Replace("\"", "\"\"")}\"" : a;
    csv.AppendLine($"{qEscaped};{aEscaped};ТПП;Часто задаваемые вопросы ответы  КЦ ТПП 2026.docx");
}
File.WriteAllText(outputCsv, csv.ToString(), new UTF8Encoding(true)); // UTF-8 with BOM
Console.WriteLine($"CSV saved to: {outputCsv}");

// Generate Markdown
var md = new StringBuilder();
md.AppendLine("# Часто задаваемые вопросы (КЦ ТПП, 2026)");
md.AppendLine();
md.AppendLine("**Источник:** Часто задаваемые вопросы ответы  КЦ ТПП 2026.docx");
md.AppendLine();
md.AppendLine("---");
md.AppendLine();

for (int i = 0; i < qaPairs.Count; i++)
{
    var (q, a) = qaPairs[i];
    md.AppendLine($"## {i + 1}. {q}");
    md.AppendLine();
    md.AppendLine(a);
    md.AppendLine();
    md.AppendLine("---");
    md.AppendLine();
}

File.WriteAllText(outputMd, md.ToString(), new UTF8Encoding(true)); // UTF-8 with BOM
Console.WriteLine($"Markdown saved to: {outputMd}");

// Print first 3 and last 3 for verification
Console.WriteLine("\n=== First 3 Q&A pairs ===");
for (int i = 0; i < 3; i++)
{
    var (q, a) = qaPairs[i];
    Console.WriteLine($"\n--- Q{i + 1} ---");
    Console.WriteLine($"Q: {q}");
    Console.WriteLine($"A: {a.Substring(0, Math.Min(150, a.Length))}...");
}

Console.WriteLine("\n=== Last 3 Q&A pairs ===");
for (int i = qaPairs.Count - 3; i < qaPairs.Count; i++)
{
    var (q, a) = qaPairs[i];
    Console.WriteLine($"\n--- Q{i + 1} ---");
    Console.WriteLine($"Q: {q}");
    Console.WriteLine($"A: {a.Substring(0, Math.Min(150, a.Length))}...");
}