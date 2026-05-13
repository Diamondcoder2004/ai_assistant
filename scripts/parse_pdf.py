"""
PDF -> Markdown through LlamaCloud REST API.
Part of ai_assistant ingestion pipeline.
"""
import os
import re
import time
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.cloud.llamaindex.ai"


# ── API helpers ──────────────────────────────────────────────────────────────

def _api_key() -> str:
    key = os.getenv("LLAMA_CLOUD_API_KEY")
    if not key:
        raise RuntimeError("LLAMA_CLOUD_API_KEY not found in .env")
    return key


def _headers(api_key: str, content_type: Optional[str] = None) -> dict:
    h = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
    if content_type:
        h["Content-Type"] = content_type
    return h


def upload_file(api_key: str, file_path: str) -> str:
    url = f"{BASE_URL}/api/v1/beta/files"
    headers = {"Authorization": f"Bearer {api_key}"}
    name = Path(file_path).name
    print(f"  [UPLOAD] Uploading: {name}...")
    with open(file_path, "rb") as f:
        resp = requests.post(
            url, headers=headers,
            files={"file": (name, f, "application/pdf")},
            data={"purpose": "parse"},
            timeout=120,
        )
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Upload failed [{resp.status_code}]: {resp.text}")
    file_id = resp.json()["id"]
    print(f"  [OK] Uploaded (file_id: {file_id})")
    return file_id


def create_parse_job(api_key: str, file_id: str, tier: str = "agentic") -> str:
    url = f"{BASE_URL}/api/v2/parse"
    payload = {
        "file_id": file_id,
        "tier": tier,
        "version": "latest",
        "output_options": {
            "markdown": {"tables": {"merge_continued_tables": True}}
        },
        "processing_options": {
            "cost_optimizer": {"enable": True},
            "ocr_parameters": {"languages": ["rs_cyrillic"]},
        },
    }
    print(f"  [JOB] Creating parse job (tier={tier})...")
    resp = requests.post(
        url, headers=_headers(api_key, "application/json"), json=payload, timeout=60
    )
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Job creation failed [{resp.status_code}]: {resp.text}")
    result = resp.json()
    job_id = result["id"]
    print(f"  [OK] Job created (job_id: {job_id}, status: {result.get('status')})")
    return job_id


def wait_for_completion(api_key: str, job_id: str, timeout: int = 600) -> None:
    url = f"{BASE_URL}/api/v2/parse/{job_id}"
    headers = _headers(api_key)
    print(f"  [WAIT] Waiting for completion (timeout: {timeout}s)...")
    start = time.time()
    interval = 2.0
    polls = 0
    while True:
        elapsed = time.time() - start
        if elapsed > timeout:
            raise TimeoutError(f"Parsing timed out after {timeout}s")
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code != 200:
            print(f"  [WARN] Status check error: {resp.status_code}")
            time.sleep(interval)
            continue
        result = resp.json()
        job_data = result.get("job", result)
        status = job_data.get("status", "UNKNOWN")
        polls += 1
        if polls % 5 == 0:
            print(f"     ... {status} ({elapsed:.0f}s)")
        if status == "COMPLETED":
            print(f"  [OK] Completed in {elapsed:.1f}s")
            return
        if status in ("FAILED", "CANCELLED"):
            raise RuntimeError(f"Job {status}: {job_data.get('error_message', 'unknown')}")
        time.sleep(interval)
        if polls % 5 == 0 and interval < 10:
            interval += 1


def get_parse_result(api_key: str, job_id: str) -> str:
    url = f"{BASE_URL}/api/v2/parse/{job_id}"
    params = {"expand": ["markdown_full", "text_full"]}
    print("  [FETCH] Fetching result...")
    resp = requests.get(
        url, headers=_headers(api_key), params=params, timeout=120
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Get result failed [{resp.status_code}]: {resp.text}")
    result = resp.json()

    markdown = result.get("markdown_full", "")
    if not markdown:
        md_data = result.get("markdown", {})
        if isinstance(md_data, dict):
            pages = [p.get("markdown", "") for p in md_data.get("pages", []) if isinstance(p, dict)]
            markdown = "\n\n---\n\n".join(pages)
    if not markdown:
        markdown = result.get("text_full", "")
    return markdown


# ── Post-processing ──────────────────────────────────────────────────────────

def post_process_markdown(md: str) -> str:
    md = md.replace("ROW_SPAN_CONTINUE<br/>", "")
    md = md.replace("ROW_SPAN_CONTINUE", "")

    def convert_latex_in_cell(content: str) -> str:
        content = re.sub(r"\\text\{([^}]*)\}", r"\1", content)

        def latex_to_html(m):
            base, sub, sup = m.group(1), m.group(2), m.group(3)
            sub = re.sub(r"\\text\{([^}]*)\}", r"\1", sub)
            sup = re.sub(r"\\text\{([^}]*)\}", r"\1", sup)
            return f"{base}<sub>{sub}</sub><sup>{sup}</sup>"

        content = re.sub(
            r"\$([A-Za-zА-Яа-я])_\{([^}]*)\}\^\{([^}]*)\}\$", latex_to_html, content
        )

        def latex_sub_only(m):
            base, sub = m.group(1), m.group(2)
            sub = re.sub(r"\\text\{([^}]*)\}", r"\1", sub)
            return f"{base}<sub>{sub}</sub>"

        content = re.sub(r"\$([A-Za-zА-Яа-я])_\{([^}]*)\}\$", latex_sub_only, content)
        return content

    md = re.sub(r"<td>(.*?)</td>", lambda m: f"<td>{convert_latex_in_cell(m.group(1))}</td>", md, flags=re.DOTALL)
    md = re.sub(r"<th>(.*?)</th>", lambda m: f"<th>{convert_latex_in_cell(m.group(1))}</th>", md, flags=re.DOTALL)
    md = re.sub(r"\\text\{([^}]*)\}", r"\1", md)
    return md


# ── Main entry ───────────────────────────────────────────────────────────────

def parse_pdf_to_markdown(pdf_path: str, output_dir: str, tier: str = "agentic") -> str:
    """
    Parse a single PDF to Markdown and save it.
    Returns the output file path.
    """
    input_file = Path(pdf_path)
    if not input_file.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    output_file = out_dir / (input_file.stem + ".md")
    file_size_mb = input_file.stat().st_size / (1024 * 1024)

    print(f"{'='*60}")
    print(f"[PDF] {input_file.name}  ({file_size_mb:.1f} MB)")
    print(f"   ->  {output_file}")
    print(f"{'='*60}")

    key = _api_key()
    file_id = upload_file(key, str(input_file))
    job_id = create_parse_job(key, file_id, tier)
    wait_for_completion(key, job_id)
    markdown = get_parse_result(key, job_id)

    if not markdown.strip():
        raise ValueError("Parsing returned empty result")

    print("  [POSTPROC] Post-processing...")
    markdown = post_process_markdown(markdown)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(markdown)

    chars = len(markdown)
    lines = markdown.count("\n")
    tables = markdown.count("|---|")
    print(f"  [OK] Saved: {chars:,} chars, {lines:,} lines, {tables} tables")
    return str(output_file)


if __name__ == "__main__":
    import sys

    project_root = Path(__file__).resolve().parent.parent
    source_dir = project_root / "new_data" / "source"
    output_dir = source_dir / "markdown_data"

    if len(sys.argv) > 1:
        arg = sys.argv[1]
        candidate = source_dir / arg
        # If arg points to a .pdf file -> parse single file
        if candidate.suffix.lower() == ".pdf" and candidate.exists():
            pdf_files = [candidate]
            desc = arg
        elif candidate.is_dir():
            pdf_files = sorted(candidate.glob("*.pdf"))
            desc = arg
        else:
            print(f"Error: {arg} is neither a PDF file nor a directory")
            sys.exit(1)
    else:
        # Default: operational/instructions
        pdf_dir = source_dir / "operational" / "instructions"
        pdf_files = sorted(pdf_dir.glob("*.pdf"))
        desc = "operational/instructions"

    if not pdf_files:
        print("No PDF files found")
        sys.exit(1)

    print(f"Found {len(pdf_files)} PDF(s) to parse in {desc}\n")

    for pdf in pdf_files:
        try:
            parse_pdf_to_markdown(str(pdf), str(output_dir))
        except Exception as e:
            print(f"[FAIL] FAILED: {pdf.name} — {e}")

    print("\n[DONE] Done.")
