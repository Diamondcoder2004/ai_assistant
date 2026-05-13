#r "nuget: DocumentFormat.OpenXml, 3.2.0"

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

// Extract all paragraphs and their text
var paragraphs = body.Elements<Paragraph>().ToList();

Console.WriteLine($"Total paragraphs: {paragraphs.Count}");

// Pattern to identify questions - typically they have bold text or are numbered like "1.", "2.", etc.
var questionPatterns = new[]
{
    @"^\s*(\d+)[.\)]\s*",           // "1. " or "1) " at start
    @"^Вопрос\s*\d+",               // "Вопрос 1"
    @"^Q\d+",                        // "Q1"
};

bool IsQuestion(Paragraph p)
{
    var text = p.InnerText.Trim();
    if (string.IsNullOrWhiteSpace(text)) return false;
    
    // Check if starts with a number followed by dot/bracket
    if (Regex.IsMatch(text, @"^\d+[.\)]\s+"))
        return true;
    
    // Check if text starts with question words
    var questionWords = new[] { "как", "что", "где", "когда", "почему", "зачем", "сколько", "какой", "какая", "какие", "кто", "можно", "нужно", "необходимо", "является", "относится", "входит", "составляет" };
    var lowerText = text.ToLower();
    return questionWords.Any(w => lowerText.StartsWith(w) || lowerText.StartsWith("?" + w));
}

// Extract Q&A pairs
var qaPairs = new List<(string Question, string Answer)>();
string currentQuestion = "";
string currentAnswer = "";
bool inAnswer = false;

foreach (var para in paragraphs)
{
    var text = para.InnerText.Trim();
    if (string.IsNullOrWhiteSpace(text)) continue;
    
    // Check formatting - is this bold/large text indicating a question?
    var isBold = para.Descendants<Bold>().Any();
    var fontSize = para.Descendants<RunProperties>()
        .Select(rp => rp.FontSize?.Val?.Value)
        .FirstOrDefault();
    
    // Check if this paragraph looks like a question header
    var isNumberedHeader = Regex.IsMatch(text, @"^\d+\s*$)");
    
    if (IsQuestion(para) || (isBold && text.Length < 200))
    {
        // Save previous Q&A if exists
        if (!string.IsNullOrWhiteSpace(currentQuestion))
        {
            qaPairs.Add((currentQuestion.Trim(), currentAnswer.Trim()));
        }
        currentQuestion = text;
        currentAnswer = "";
        inAnswer = true;
    }
    else if (inAnswer)
    {
        // Append to answer
        if (!string.IsNullOrWhiteSpace(currentAnswer))
            currentAnswer += "\n";
        currentAnswer += text;
    }
    else if (string.IsNullOrWhiteSpace(currentQuestion))
    {
        // This is before any question - treat as intro, skip
        continue;
    }
}

// Add last Q&A pair
if (!string.IsNullOrWhiteSpace(currentQuestion))
{
    qaPairs.Add((currentQuestion.Trim(), currentAnswer.Trim()));
}

Console.WriteLine($"Found {qaPairs.Count} Q&A pairs");

// Generate CSV
var csv = new StringBuilder();
csv.AppendLine("question;answer;category;source");
foreach (var (q, a) in qaPairs)
{
    // Escape fields containing semicolons or newlines
    var qEscaped = q.Contains(';') || q.Contains('\n') ? $"\"{q.Replace("\"", "\"\"")}\"" : q;
    var aEscaped = a.Contains(';') || a.Contains('\n') ? $"\"{a.Replace("\"", "\"\"")}\"" : a;
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

// Print first few for verification
Console.WriteLine("\n=== First 3 Q&A pairs ===");
for (int i = 0; i < Math.Min(3, qaPairs.Count); i++)
{
    var (q, a) = qaPairs[i];
    Console.WriteLine($"\n--- Q{i + 1} ---");
    Console.WriteLine($"Q: {q.Substring(0, Math.Min(100, q.Length))}...");
    Console.WriteLine($"A: {a.Substring(0, Math.Min(100, a.Length))}...");
}