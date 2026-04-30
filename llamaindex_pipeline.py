#!/usr/bin/env python3
"""LlamaIndex RAG pipeline for d-inference knowledge extraction.

Produces structured component analyses + dependency graph from the codebase,
using Ollama embeddings + GLM-5.1 via OpenRouter.
"""

import json
import os
import sys
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────────
REPO_PATH = Path("/tmp/d-inference")
OUTPUT_DIR = Path("artifacts/d-inference-llamaindex")
EMBED_MODEL = "nomic-embed-text"
LLM_MODEL = "z-ai/glm-5.1"
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50

# ── Ensure API key ──────────────────────────────────────────────────────────
hermes_env = Path(os.path.expanduser("~/.hermes/.env"))
if not os.environ.get("OPENROUTER_API_KEY") and hermes_env.exists():
    for line in hermes_env.read_text().splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            os.environ["OPENROUTER_API_KEY"] = line.split("=", 1)[1]
            os.environ["OPENAI_API_KEY"] = os.environ["OPENROUTER_API_KEY"]
            break

if not os.environ.get("OPENROUTER_API_KEY"):
    print("ERROR: OPENROUTER_API_KEY not found"); sys.exit(1)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Build index ─────────────────────────────────────────────────────────────
from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage,
    Settings,
    PromptTemplate,
)
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.openrouter import OpenRouter

print("🔧 Configuring LlamaIndex...")
Settings.embed_model = OllamaEmbedding(
    model_name=EMBED_MODEL,
    base_url="http://localhost:11434",
)
Settings.llm = OpenRouter(
    model=LLM_MODEL,
    temperature=0.1,
    max_tokens=4096,
    context_window=32768,
)
Settings.chunk_size = CHUNK_SIZE
Settings.chunk_overlap = CHUNK_OVERLAP

# Check for cached index
INDEX_DIR = OUTPUT_DIR / ".index_cache"
if INDEX_DIR.exists() and any(INDEX_DIR.iterdir()):
    print("📦 Loading cached index...")
    storage_context = StorageContext.from_defaults(persist_dir=str(INDEX_DIR))
    index = load_index_from_storage(storage_context)
else:
    print("📂 Loading documents from d-inference...")
    # Load specific key dirs for better signal
    reader = SimpleDirectoryReader(
        input_dir=str(REPO_PATH),
        recursive=True,
        required_exts=[
            ".go", ".rs", ".py", ".swift", ".ts", ".tsx", ".js",
            ".toml", ".yaml", ".yml", ".md", ".json", ".mod",
        ],
        exclude=[
            "*/node_modules/*",
            "*/.git/*",
            "*/target/*",
            "*/.next/*",
            "*/dist/*",
            "*/vendor/*",
            "*/generated/*",
            "*_test.go",
            "*_test.rs",
        ],
    )
    docs = reader.load_data()
    print(f"   Loaded {len(docs)} documents")

    print("🔍 Building vector index with Ollama embeddings...")
    index = VectorStoreIndex.from_documents(docs, show_progress=True)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    index.storage_context.persist(persist_dir=str(INDEX_DIR))
    print(f"   Index cached to {INDEX_DIR}")

# ── Component extraction ────────────────────────────────────────────────────
COMPONENTS = {
    "coordinator": "Go control plane: HTTP/WebSocket handlers, routing, billing, attestation, auth",
    "provider": "Rust agent: local inference proxy, coordinator client, hardware detection, security",
    "image-bridge": "Python FastAPI: OpenAI-compatible image generation bridge to Draw Things gRPC",
    "enclave": "Swift Secure Enclave helper: key management, attestation, FFI bridge",
    "console-ui": "Next.js 16 frontend: chat, billing, models, provider management",
    "e2e-encryption": "X25519 request encryption: coordinator/provider key exchange, NaCl Box",
    "attestation": "Secure Enclave + MDA verification: device identity, 4-layer attestation chain",
    "billing": "Stripe + Solana USDC: deposits, pricing, referrals, internal ledger",
    "mdm-enrollment": "MicroMDM + ACME: device enrollment, certificate provisioning",
    "protocol": "WebSocket message types: shared between coordinator and provider",
}

COMPONENT_PROMPT = PromptTemplate(
    """You are analyzing the DarkBloom/d-inference decentralized inference codebase.

Analyze the following component: {component_name}
Description: {component_desc}

Using the retrieved code context below, produce a structured analysis with:

## Overview
2-3 sentence summary of what this component does and its role in the system.

## Architecture
Key submodules/files and their responsibilities. Be specific about file paths.

## Dependencies
What other d-inference components does this depend on? List them with brief descriptions of the dependency relationship.

## API Surface
Key functions, types, or endpoints this component exposes to the rest of the system.

## Security Considerations
Any security-relevant patterns (auth, encryption, attestation, validation).

## Data Flow
How data flows through this component — trace a request from entry to exit.

Retrieved context:
{context_str}

Analysis:"""
)

DEP_GRAPH_PROMPT = PromptTemplate(
    """You are analyzing the DarkBloom/d-inference decentralized inference codebase.

Based on the retrieved code context, identify the actual import/call dependencies 
between these components:
- coordinator (Go)
- provider (Rust)
- image-bridge (Python)
- enclave (Swift)
- console-ui (Next.js)
- protocol (shared types)
- e2e-encryption (X25519/NaCl)
- attestation (Secure Enclave)
- billing (Stripe/Solana)
- mdm-enrollment (MicroMDM/ACME)

For each dependency, specify:
1. Source component
2. Target component  
3. Nature of dependency (imports, calls, data flow, configuration)

Output as a JSON array of objects with keys: source, target, nature, description

Retrieved context:
{context_str}

Dependency graph:"""
)

ARCH_PROMPT = PromptTemplate(
    """You are analyzing the DarkBloom/d-inference decentralized inference codebase.

Produce a system-level architecture document covering:

1. **System Topology**: How the 5 major services (coordinator, provider, image-bridge, enclave, console-ui) connect and communicate.
2. **Trust Boundaries**: Where data crosses trust boundaries (network, process, enclave). What cryptographic protections apply?
3. **Request Lifecycle**: Trace a consumer chat completion request from the console-ui through coordinator to provider and back. Include encryption/decryption steps.
4. **Provider Onboarding Flow**: How a new provider machine joins the network (enrollment, attestation, key provisioning).
5. **Billing Flow**: How consumers pay and providers get paid.

Be specific about code paths, file names, and function names where relevant.

Retrieved context:
{context_str}

Architecture document:"""
)

# ── Run queries ─────────────────────────────────────────────────────────────
query_engine = index.as_query_engine(similarity_top_k=8)

print("\n📊 Generating component analyses...")
analyses = {}
for comp_name, comp_desc in COMPONENTS.items():
    print(f"   Analyzing {comp_name}...", flush=True)
    try:
        response = query_engine.query(
            COMPONENT_PROMPT.format(
                component_name=comp_name,
                component_desc=comp_desc,
                context_str="",  # RAG handles this
            )
        )
        analyses[comp_name] = str(response)
# Save each component analysis immediately as it's generated
        out_path = OUTPUT_DIR / f"{comp_name}.md"
        out_path.write_text(analyses[comp_name])
        print(f"   ✓ {comp_name}: {len(analyses[comp_name])} chars", flush=True)
    except Exception as e:
        print(f"   ✗ {comp_name}: {e}")
        analyses[comp_name] = f"ERROR: {e}"

print("\n🔗 Generating dependency graph...")
try:
    dep_response = query_engine.query(
        DEP_GRAPH_PROMPT.format(context_str="")
    )
    dep_text = str(dep_response)
    # Try to extract JSON from response
    import re
    json_match = re.search(r'\[.*\]', dep_text, re.DOTALL)
    if json_match:
        dep_graph = json.loads(json_match.group())
    else:
        dep_graph = {"raw": dep_text}
    (OUTPUT_DIR / "dependency_graph.json").write_text(
        json.dumps(dep_graph, indent=2)
    )
    print(f"   ✓ Saved dependency_graph.json ({len(dep_graph) if isinstance(dep_graph, list) else 'N/A'} edges)")
except Exception as e:
    print(f"   ✗ Dependency graph failed: {e}")

print("\n🏗️ Generating architecture document...")
try:
    arch_response = query_engine.query(
        ARCH_PROMPT.format(context_str="")
    )
    (OUTPUT_DIR / "architecture.md").write_text(str(arch_response))
    print(f"   ✓ Saved architecture.md ({len(str(arch_response))} chars)")
except Exception as e:
    print(f"   ✗ Architecture doc failed: {e}")

# ── Summary ─────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("DONE. Output in:", OUTPUT_DIR)
print("Files:")
for f in sorted(OUTPUT_DIR.iterdir()):
    if f.is_file() and not f.name.startswith("."):
        print(f"  {f.name}: {f.stat().st_size:,} bytes")
